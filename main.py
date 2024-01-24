import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pytube import YouTube
import subprocess
import os
import sys
import random

def get_user_input():
    print("Wähle eine Option:")
    print("1: Unscharfer Hintergrund")
    print("2: Zwei Videos übereinander")
    option = input("Gib die Nummer deiner Option ein: ")
    return int(option)

def get_second_video_url(option):
    if option == 2:
        return input("Gib die URL des zweiten YouTube-Videos ein: ")
    return None

# Funktion, um zu überprüfen, ob FFmpeg installiert ist
def is_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

# Funktion, um FFmpeg zu installieren (falls gewünscht)
def install_ffmpeg():
    print("FFmpeg ist nicht installiert. Bitte installieren Sie FFmpeg, um fortzufahren.")
    choice = input("Möchten Sie eine Anleitung zur Installation von FFmpeg erhalten? (ja/nein): ")
    if choice.lower() == 'ja':
        print("Bitte besuchen Sie https://ffmpeg.org/download.html, um FFmpeg herunterzuladen und zu installieren.")
        sys.exit()

# Funktion, um ein YouTube-Video herunterzuladen
def download_video(url, path):
    print("Das Video wird heruntergeladen...")
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    return stream.download(output_path=path)

# Funktion, um das Video zu skalieren und in 2-Minuten-Abschnitte zu teilen
def process_video(filename, path):
    print("Das Video wird verarbeitet...")
    # Dateiname für das skalierte Video
    scaled_filename = "scaled_" + filename

    # FFmpeg-Befehl, um das Video zu skalieren, unscharfe Ränder hinzuzufügen
    ffmpeg_cmd = (
        f'ffmpeg -i "{path}/{filename}" '
        f'-filter_complex '
        f'"[0:v]scale=720:1280,boxblur=20:1,crop=720:1280[blurred]; '  # Skalieren, unscharf machen und beschneiden für den Hintergrund
        f'[0:v]scale=720:-2[sharp]; '  # Skalieren des Vordergrunds ohne Unscharfheit
        f'[blurred]scale=720:1280[bg]; '  # Skalieren des unscharfen Hintergrunds auf die volle Größe
        f'[bg][sharp]overlay=(W-w)/2:(H-h)/2" '  # Überlagern des scharfen Vordergrunds über den unscharfen Hintergrund
        f'-aspect 9:16 '  # Festlegen des Seitenverhältnisses auf 9:16
        f'-c:v libx264 -crf 18 -preset veryfast '  # Höhere Qualität bei der Kodierung (slow) schnell (veryfast)
        f'-c:a copy '  # Audio beibehalten
        f'"{path}/{scaled_filename}"'
    )
    os.system(ffmpeg_cmd)

    # Video in 2-Minuten-Abschnitte teilen
    os.system(f'ffmpeg -i "{path}/{scaled_filename}" -c copy -segment_time 120 -f segment -reset_timestamps 1 "{path}/output%03d.mp4"')
    print("Die Verarbeitung des Videos ist abgeschlossen.")

def get_video_duration_and_start(first_duration, second_filename, path, segment_length=120):
    second_duration = get_video_duration(second_filename, path)
    max_start = int(second_duration) - int(first_duration)
    start = random.randint(0, max(max_start, 0))
    return second_duration, start

def get_video_duration(filename, path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", f"{path}/{filename}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def combine_videos(first_video, second_video, path):
    print("Die Videos werden kombiniert...")
    combined_filename = "combined_" + first_video

    first_duration = get_video_duration(first_video, path)
    _, start = get_video_duration_and_start(first_duration, second_video, path)

    # Verbesserte FFmpeg-Einstellungen für höhere Qualität
    ffmpeg_cmd = (
        f'ffmpeg -i "{path}/{first_video}" -ss {start} -t {first_duration} -i "{path}/{second_video}" '
        f'-filter_complex '
        f'"[0:v]scale=-2:ih[top]; [1:v]scale=-2:ih[bottom]; [top][bottom]vstack,format=yuv420p" '
        f'-c:v libx264 -crf 18 -preset veryfast '  # Höhere Qualität bei der Kodierung (slow) schnell (veryfast
        f'-c:a aac -b:a 192k '  # Bessere Audioqualität
        f'"{path}/{combined_filename}"'
    )
    os.system(ffmpeg_cmd)

    # Teilen des kombinierten Videos in 2-Minuten-Segmente
    segment_cmd = (
        f'ffmpeg -i "{path}/{combined_filename}" -c copy -map 0 '
        f'-segment_time 120 -f segment -reset_timestamps 1 '
        f'"{path}/combined_output%03d.mp4"'
    )
    os.system(segment_cmd)
    print("Die Videos wurden erfolgreich kombiniert und segmentiert.")

# GUI-Klasse
class YouTubeDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("YouTube Video Downloader")
        self.create_widgets()

    def create_widgets(self):
        self.option_var = tk.IntVar()
        self.option_var.trace("w", self.update_option)

        self.label = tk.Label(self.master, text="YouTube Video Downloader")
        self.label.pack()

        self.option_frame = tk.Frame(self.master)
        self.option_frame.pack(pady=10)

        self.option1_rb = tk.Radiobutton(self.option_frame, text="Unscharfer Hintergrund", variable=self.option_var, value=1)
        self.option1_rb.pack(side=tk.LEFT)

        self.option2_rb = tk.Radiobutton(self.option_frame, text="Zwei Videos übereinander", variable=self.option_var, value=2)
        self.option2_rb.pack(side=tk.LEFT)

        self.url_frame = tk.Frame(self.master)
        self.url_frame.pack(pady=10)

        self.url_label1 = tk.Label(self.url_frame, text="Erstes Video URL:")
        self.url_label1.pack()
        self.url_entry1 = tk.Entry(self.url_frame)
        self.url_entry1.pack()

        self.url_label2 = tk.Label(self.url_frame, text="Zweites Video URL:")
        self.url_entry2 = tk.Entry(self.url_frame)
        self.url_entry2.insert(0, "https://www.youtube.com/watch?v=NX-i0IWl3yg")

        self.path_label = tk.Label(self.master, text="Speicherpfad:")
        self.path_label.pack()
        self.path_entry = tk.Entry(self.master)
        self.path_entry.insert(0, r"C:\Users\Fabian Miller\Videos")


        self.path_entry.pack()

        self.browse_button = tk.Button(self.master, text="Durchsuchen", command=self.browse_folder)
        self.browse_button.pack()

        self.download_button = tk.Button(self.master, text="Download", command=self.download)
        self.download_button.pack()

        # Initial update of the option
        self.update_option()

    def update_option(self, *args):
        option = self.option_var.get()
        if option == 2:
            self.url_label2.pack()
            self.url_entry2.pack()
        else:
            self.url_label2.pack_forget()
            self.url_entry2.pack_forget()
    def download(self):
        option = self.option_var.get()
        url1 = self.url_entry1.get()
        url2 = self.url_entry2.get()
        path = self.path_entry.get()

        if not url1 or not path:
            messagebox.showwarning("Warnung", "Bitte geben Sie mindestens eine URL und einen Speicherpfad an.")
            return

        try:
            filename1 = download_video(url1, path)
            filename1 = os.path.basename(filename1)

            if option == 1:
                process_video(filename1, path)
            elif option == 2 and url2:
                filename2 = download_video(url2, path)
                filename2 = os.path.basename(filename2)
                combine_videos(filename1, filename2, path)

            messagebox.showinfo("Erfolg", "Download und Verarbeitung abgeschlossen.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_selected)

def main():
    if not is_ffmpeg_installed():
        install_ffmpeg()

    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()