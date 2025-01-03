import os
import threading
import json
from yt_dlp import YoutubeDL
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CONFIG_PATH = "config.json"

def charger_configuration():
    return json.load(open(CONFIG_PATH, "r")) if os.path.exists(CONFIG_PATH) else {"dossier": "musiques", "format": "mp3"}

def sauvegarder_configuration(config):
    with open(CONFIG_PATH, "w") as file:
        json.dump(config, file)

def telecharger_audio(url, dossier, format_audio, log, progress, stop_event, total, current):
    if stop_event.is_set():
        return
    options = {
        'format': 'bestaudio/best',
        'outtmpl': f'{dossier}/%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': format_audio}],
        'quiet': True,
    }
    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url)
            log.insert(tk.END, f"✅ Téléchargé : {info.get('title', 'Inconnu')}\n")
            progress.set(((current + 1) / total) * 100)
            log.see(tk.END)
    except Exception as e:
        log.insert(tk.END, f"❌ Erreur avec {url}: {e}\n")
        log.see(tk.END)

def lancer_telechargement(liens, dossier, format_audio, log, progress, stop_event):
    def worker():
        if not os.path.exists(dossier):
            os.makedirs(dossier)
        try:
            playlist = []
            progress.set(0)
            log.insert(tk.END, f"Vérification du nombre de vidéos...\n")
            with YoutubeDL({'quiet': True}) as ydl:
                for lien in liens:
                    info = ydl.extract_info(lien, download=False)
                    playlist += [entry['webpage_url'] for entry in info['entries']] if 'entries' in info else [lien]
            total = len(playlist)
            log.insert(tk.END, f"Total de vidéos à télécharger : {total}\n")
            for i, lien in enumerate(playlist):
                if stop_event.is_set():
                    log.insert(tk.END, "🚫 Téléchargement arrêté.\n")
                    break
                telecharger_audio(lien, dossier, format_audio, log, progress, stop_event, total, i)
            if not stop_event.is_set():
                log.insert(tk.END, "✅ Tous les téléchargements sont terminés !\n")
        except Exception as e:
            log.insert(tk.END, f"❌ Erreur : {e}\n")
    threading.Thread(target=worker).start()

def creer_interface():
    config = charger_configuration()
    stop_event = threading.Event()

    root = tk.Tk()
    root.title("Téléchargeur YouTube")
    root.geometry("700x660")

    ttk.Label(root, text="Entrez les URL YouTube (une par ligne) :").pack(pady=5)
    text_urls = tk.Text(root, width=70, height=10)
    text_urls.pack(pady=5)

    ttk.Label(root, text="Dossier de téléchargement :").pack(pady=5)
    frame_dossier = ttk.Frame(root)
    frame_dossier.pack()
    entry_dossier = ttk.Entry(frame_dossier, width=50)
    entry_dossier.insert(0, config["dossier"])
    entry_dossier.pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_dossier, text="Parcourir", command=lambda: entry_dossier.insert(0, filedialog.askdirectory())).pack(side=tk.LEFT)

    ttk.Label(root, text="Format audio :").pack(pady=5)
    format_combo = ttk.Combobox(root, values=["mp3", "aac", "wav"], state="readonly", width=10)
    format_combo.set(config["format"])
    format_combo.pack(pady=5)

    progress = tk.DoubleVar()
    ttk.Progressbar(root, variable=progress, maximum=100, length=500).pack(pady=10)

    log = tk.Text(root, width=70, height=10, state="normal")
    log.pack(pady=5)

    frame_boutons = ttk.Frame(root)
    frame_boutons.pack(pady=10)
    ttk.Button(frame_boutons, text="Démarrer", command=lambda: lancer_telechargement(
        [url.strip() for url in text_urls.get("1.0", tk.END).splitlines() if url.strip()],
        entry_dossier.get(), format_combo.get(), log, progress, stop_event)).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_boutons, text="Arrêter", command=stop_event.set).pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    creer_interface()
