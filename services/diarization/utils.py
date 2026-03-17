from pathlib import Path
import shutil

AUDIO_EXTENSIONS = [".wav", ".mp3"]
OUTPUT_EXTENSIONS = [".txt", ".srt", ".wav", ".json"]  # файлы, которые мы хотим собрать

def find_audio_files(input_path: Path):
    audio_files = []
    if input_path.is_dir():
        for ext in AUDIO_EXTENSIONS:
            audio_files.extend(input_path.glob(f"*{ext}"))
    elif input_path.is_file() and input_path.suffix.lower() in AUDIO_EXTENSIONS:
        audio_files.append(input_path)
    return audio_files

def copy_results(src_dir: Path, dest_dir: Path):
    """Копируем все файлы результата из src_dir в dest_dir"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for file in src_dir.glob("*"):
        if file.suffix.lower() in OUTPUT_EXTENSIONS:
            shutil.copy2(file, dest_dir)