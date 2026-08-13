import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
import os
import threading

from domain.audio_files import FILE_DIALOG_PATTERN
from domain.whisper_models import SUPPORTED_MODELS, DEFAULT_MODEL
from platform_.transcriber import transcribe_to_file, TranscriptionError

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
    tk.Label(loader, text="La transcription est en cours. Cela peut prendre un moment...\nPlus le modèle est lourd et l'audio est long, plus la transcription prend du temps.").pack(pady=10)
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

    def transcribe_task():
        try:
            output_path = transcribe_to_file(
                selected_file, model_factory=lambda: WhisperModel(model_choice)
            )
        except TranscriptionError as exc:
            loader.destroy()
            show_error_window(str(exc))
            return

        loader.destroy()
        show_done_window(output_path)

    threading.Thread(target=transcribe_task, daemon=True).start()

def browse_file():
    global selected_file
    path = filedialog.askopenfilename(
        title="Choisir un fichier audio",
        filetypes=[("Fichiers audio", FILE_DIALOG_PATTERN)]
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
