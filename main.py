from pytube import YouTube
import os
import subprocess
import sys

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
        f'-c:v libx264 -crf 23 -preset veryfast '  # Video-Encoder-Einstellungen
        f'-c:a copy '  # Audio beibehalten
        f'"{path}/{scaled_filename}"'
    )
    os.system(ffmpeg_cmd)

    # Video in 2-Minuten-Abschnitte teilen
    os.system(f'ffmpeg -i "{path}/{scaled_filename}" -c copy -segment_time 120 -f segment -reset_timestamps 1 "{path}/output%03d.mp4"')
    print("Die Verarbeitung des Videos ist abgeschlossen.")


# Hauptfunktion
def main():
    if not is_ffmpeg_installed():
        install_ffmpeg()

    url = input("Bitte geben Sie die URL des YouTube-Videos ein: ")
    path = r"C:\Users\Fabian Miller\Videos"  # Setzen Sie hier den Pfad, wo das Video gespeichert werden soll

    filename = download_video(url, path)
    filename = os.path.basename(filename)

    process_video(filename, path)

if __name__ == "__main__":
    main()