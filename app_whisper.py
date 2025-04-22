import tkinter as tk
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
import os

# Interface
root = tk.Tk()
root.title("Transcription Audio (Whisper)")
root.geometry("400x200")

file_path = tk.StringVar()
model_choice = tk.StringVar(value="base")



def browse_file():
    path = filedialog.askopenfilename(
        title="Choisir un fichier audio",
        filetypes=[("Fichiers audio", "*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.mkv " +
            "*.amr *.dss *.dvf *.bmf *.tta *.tak *.ape *.alac *.ra *.rm *.wma *.opus *.aac " +
            "*.pcm *.raw *.au *.aiff")]
    )
    if path:
        file_path.set(path)

def transcribe():
    path = file_path.get()
    if not os.path.isfile(path):
        messagebox.showerror("Erreur", "Aucun fichier sélectionné.")
        return

    messagebox.showinfo("Transcription", "La transcription va commencer. Cela peut prendre un moment.")
    model = WhisperModel(model_choice.get())
    segments, _ = model.transcribe(path)

    text = "\n".join([seg.text for seg in segments])
    txt_output = os.path.splitext(path)[0] + "_transcription.txt"

    with open(txt_output, "w", encoding="utf-8") as f:
        f.write(text)

    messagebox.showinfo("Terminé", f"Transcription enregistrée :\n{txt_output}")

# Widgets
tk.Label(root, text="Fichier audio :").pack(pady=5)
tk.Button(root, text="Parcourir", command=browse_file).pack()
tk.Label(root, textvariable=file_path).pack(pady=5)

tk.Label(root, text="Modèle :").pack()
tk.OptionMenu(root, model_choice, "tiny", "base", "small", "medium", "large").pack()

tk.Button(root, text="Transcrire", command=transcribe, bg="lightgreen").pack(pady=10)

root.mainloop()