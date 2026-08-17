import os

# Must run before faster_whisper (and therefore huggingface_hub) is imported.
# huggingface_hub already retries with a timeout per attempt (default 10s,
# up to 5 attempts) on its own, but a network that silently drops packets
# rather than refusing the connection (common on restrictive corporate
# proxies) can still make each attempt run close to its full timeout before
# the retry logic gives up — tightening it makes that bounded wait shorter
# without weakening it for a normal, merely slow, connection.
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "8")

import queue  # noqa: E402
import threading  # noqa: E402
import tkinter as tk  # noqa: E402
from tkinter import filedialog, messagebox  # noqa: E402

from faster_whisper import WhisperModel  # noqa: E402

from domain.audio_files import FILE_DIALOG_PATTERN  # noqa: E402
from domain.whisper_models import DEFAULT_MODEL, SUPPORTED_MODELS  # noqa: E402
from platform_.transcriber import TranscriptionError, transcribe_to_file  # noqa: E402

selected_file = None
model_choice = DEFAULT_MODEL
file_label = None
model_menu = None
root = None


def show_loader_window():
    loader = tk.Toplevel()
    loader.title("Transcription en cours")
    loader.geometry("600x70")
    loader.resizable(False, False)
    loader_text = (
        "La transcription est en cours. Cela peut prendre un moment...\n"
        "Plus le modèle est lourd et l'audio est long, plus la transcription prend du temps."
    )
    tk.Label(loader, text=loader_text).pack(pady=10)
    return loader


def show_done_window(output_path):
    def close_and_restart():
        global selected_file, model_choice
        done.destroy()
        selected_file = None
        model_choice = DEFAULT_MODEL
        file_label.config(text="Aucun fichier sélectionné.")
        model_menu.set(DEFAULT_MODEL)
        root.deiconify()

    done = tk.Toplevel()
    done.title("Terminé")
    done.geometry("350x150")
    tk.Label(done, text="✅ Transcription terminée !", font=("Arial", 14)).pack(pady=10)
    tk.Label(done, text=f"Fichier sauvegardé :\n{output_path}", wraplength=300).pack(pady=5)
    tk.Button(done, text="OK", command=close_and_restart).pack(pady=5)


def show_error_window(message):
    root.deiconify()
    messagebox.showerror("Erreur de transcription", message)


def run_transcription():
    global selected_file, model_choice

    loader = show_loader_window()
    result_queue = queue.Queue()

    def transcribe_task():
        # Runs off the main thread: must never touch Tk widgets directly
        # (Tcl/Tk is not thread-safe — doing so hangs the UI on Windows).
        # Results are handed back through a thread-safe queue instead, and
        # applied to the UI by poll_result(), which runs on the main thread.
        print("[DEBUG] transcribe_task: thread started", flush=True)
        try:
            output_path = transcribe_to_file(
                selected_file, model_factory=lambda: WhisperModel(model_choice)
            )
        except TranscriptionError as exc:
            print("[DEBUG] transcribe_task: TranscriptionError:", exc, flush=True)
            result_queue.put(("error", str(exc)))
            return

        print("[DEBUG] transcribe_task: done, queuing result", flush=True)
        result_queue.put(("done", output_path))

    def poll_result():
        try:
            status, payload = result_queue.get_nowait()
        except queue.Empty:
            loader.after(100, poll_result)
            return

        print("[DEBUG] poll_result: got", status, flush=True)
        loader.destroy()
        if status == "error":
            show_error_window(payload)
        else:
            show_done_window(payload)

    threading.Thread(target=transcribe_task, daemon=True).start()
    loader.after(100, poll_result)


def browse_file():
    global selected_file
    path = filedialog.askopenfilename(
        title="Choisir un fichier audio", filetypes=[("Fichiers audio", FILE_DIALOG_PATTERN)]
    )
    if path:
        selected_file = path
        file_label.config(text=os.path.basename(path))


def setup_main_window(root):
    global model_choice, file_label, model_menu

    root.title("Transcription Audio (Whisper)")
    root.geometry("400x220")
    root.resizable(False, False)

    file_label = tk.Label(root, text="Aucun fichier sélectionné.")
    file_label.pack(pady=10)

    tk.Button(root, text="Choisir un fichier audio", command=browse_file).pack()

    tk.Label(root, text="Modèle :").pack(pady=(20, 0))
    model_menu = tk.StringVar(value=model_choice)
    tk.OptionMenu(root, model_menu, *SUPPORTED_MODELS).pack()

    def on_transcribe():
        global model_choice
        if not selected_file:
            messagebox.showerror("Erreur", "Veuillez d'abord sélectionner un fichier audio.")
            return
        model_choice = model_menu.get()
        root.withdraw()
        run_transcription()

    tk.Button(root, text="Transcrire", command=on_transcribe, bg="lightgreen").pack(pady=20)


# 🔄 Point d'entrée principal
if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()  # ← important pour Windows et PyInstaller
    root = tk.Tk()
    setup_main_window(root)
    root.mainloop()
