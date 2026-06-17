import urllib.request
import zipfile
import os
import shutil

def setup_local_ffmpeg():
    local_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(local_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    # Si déjà installé, on ignore
    if os.path.exists(os.path.join(bin_dir, "ffmpeg.exe")) and os.path.exists(os.path.join(bin_dir, "ffprobe.exe")):
        print(f"✅ FFmpeg est déjà installé localement dans : {bin_dir}")
        return

    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(local_dir, "ffmpeg.zip")

    print(f"⬇️  Téléchargement de FFmpeg depuis {url}\n(Cela peut prendre quelques minutes, veuillez patienter...)")
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
        return

    print("📦 Extraction des exécutables...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith("ffmpeg.exe") or file_info.filename.endswith("ffprobe.exe"):
                    extracted_path = zip_ref.extract(file_info, local_dir)
                    target_path = os.path.join(bin_dir, os.path.basename(file_info.filename))
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(extracted_path, target_path)
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction : {e}")
        return

    print("🧹 Nettoyage des fichiers temporaires...")
    os.remove(zip_path)
    # Nettoyage du dossier parent extrait
    for item in os.listdir(local_dir):
        item_path = os.path.join(local_dir, item)
        if os.path.isdir(item_path) and item.startswith("ffmpeg-") and item != "bin":
            shutil.rmtree(item_path)

    print(f"🎉 FFmpeg a été installé localement avec succès dans : {bin_dir}")

if __name__ == "__main__":
    setup_local_ffmpeg()
