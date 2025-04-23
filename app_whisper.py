import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
import os
import threading
import time

selected_file = None
model_choice = "base"

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
        model_choice = "base"
        file_label.config(text="Aucun fichier sélectionné.")
        root.deiconify()

    done = tk.Toplevel()
    done.title("Terminé")
    done.geometry("350x150")
    tk.Label(done, text="✅ Transcription terminée !", font=("Arial", 14)).pack(pady=10)
    tk.Label(done, text=f"Fichier sauvegardé :\n{output_path}", wraplength=300).pack(pady=5)
    tk.Button(done, text="OK", command=close_and_restart).pack(pady=5)

def run_transcription():
    global selected_file, model_choice

    loader = show_loader_window()

    def transcribe_task():
        model = WhisperModel(model_choice)
        segments, _ = model.transcribe(selected_file)

        text = "\n".join([seg.text for seg in segments])
        txt_output = os.path.splitext(selected_file)[0] + "_transcription.txt"

        with open(txt_output, "w", encoding="utf-8") as f:
            f.write(text)

        loader.destroy()
        show_done_window(txt_output)

    threading.Thread(target=transcribe_task, daemon=True).start()

def browse_file():
    global selected_file
    path = filedialog.askopenfilename(
        title="Choisir un fichier audio",
        filetypes=[("Fichiers audio", "*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.mkv " +
            "*.amr *.dss *.dvf *.bmf *.tta *.tak *.ape *.alac *.ra *.rm *.wma *.opus *.aac " +
            "*.pcm *.raw *.au *.aiff")]
    )
    if path:
        selected_file = path
        file_label.config(text=os.path.basename(path))

def launch_main_window():
    global model_choice, file_label, selected_file, root

    root = tk.Tk()
    root.title("Transcription Audio (Whisper)")
    root.geometry("400x220")
    root.resizable(False, False)

    file_label = tk.Label(root, text="Aucun fichier sélectionné.")
    file_label.pack(pady=10)

    tk.Button(root, text="Choisir un fichier audio", command=browse_file).pack()

    tk.Label(root, text="Modèle :").pack(pady=(20, 0))
    model_menu = tk.StringVar(value=model_choice)
    tk.OptionMenu(root, model_menu, "tiny", "base", "small", "medium", "large").pack()

    def on_transcribe():
        nonlocal model_menu
        global model_choice, root
        if not selected_file:
            messagebox.showerror("Erreur", "Veuillez d'abord sélectionner un fichier audio.")
            return
        model_choice = model_menu.get()
        root.withdraw()
        run_transcription()

    tk.Button(root, text="Transcrire", command=on_transcribe, bg="lightgreen").pack(pady=20)

    root.mainloop()

launch_main_window()
