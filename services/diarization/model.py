import subprocess
from pathlib import Path
import shutil

# BASE_DIR — корень проекта, относительно model.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent  
# model.py находится в services/diarization_new/
# поэтому parent.parent.parent → /home/user/wav-parser

# Путь к скрипту whisper-diarization
DIARIZE_SCRIPT = BASE_DIR / "external/whisper-diarization/diarize.py"

WHISPER_MODEL = "large-v3"
BATCH_SIZE = 4
# WHISPER_MODEL = "base"
LANGUAGE = "ru"
AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac"]
OUTPUT_EXTENSIONS = [".txt", ".srt"]  # файлы для перемещения после обработки


def extract_numeric_id(file_path: Path) -> str:
    """Берем имя файла и извлекаем числовой идентификатор"""
    stem = file_path.stem
    return stem.split("_")[0]


def run_diarization(audio_file: Path, output_dir: Path):
    """
    Запускаем whisper-diarization для одного файла
    и перемещаем результаты (.txt, .srt) в output_dir
    """
    file_id = extract_numeric_id(audio_file)
    audio_result_dir = output_dir / file_id
    audio_result_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "python",
        str(DIARIZE_SCRIPT),
        "-a",
        str(audio_file),
        "--whisper-model",
        WHISPER_MODEL,
        "--language",
        LANGUAGE,
        "--no-stem",
        "--batch-size",
        str(BATCH_SIZE)
    ]

    print(f"\n🔊 Обрабатываем: {audio_file}")
    subprocess.run(command, check=True)
    print(f"✅ whisper-diarization завершил обработку: {audio_file.name}")

    # --- перенос .txt и .srt в audio_result_dir ---
    for ext in OUTPUT_EXTENSIONS:
        src_file = audio_file.parent / f"{audio_file.stem}{ext}"
        if src_file.exists():
            dst_file = audio_result_dir / src_file.name
            shutil.move(str(src_file), str(dst_file))
            print(f"📄 {src_file.name} перемещён в {audio_result_dir}")