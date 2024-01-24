from pytube import YouTube
import os
import subprocess
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


# Hauptfunktion
def main():
    if not is_ffmpeg_installed():
        install_ffmpeg()

    option = get_user_input()
    path = r"C:\Users\Fabian Miller\Videos"  # Setzen Sie hier den Pfad, wo das Video gespeichert werden soll

    if option == 1:
        url = input("Bitte geben Sie die URL des YouTube-Videos ein: ")
        filename = download_video(url, path)
        filename = os.path.basename(filename)
        process_video(filename, path)

    elif option == 2:
        url1 = input("Bitte geben Sie die URL des ersten YouTube-Videos ein: ")
        url2 = input("Bitte geben Sie die URL des zweiten YouTube-Videos ein: ")
        filename1 = download_video(url1, path)
        filename2 = download_video(url2, path)
        filename1 = os.path.basename(filename1)
        filename2 = os.path.basename(filename2)
        combine_videos(filename1, filename2, path)

    else:
        print("Ungültige Option ausgewählt.")

# Überarbeitete combine_videos-Funktion
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

if __name__ == "__main__":
    main()
