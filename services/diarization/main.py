import argparse
from pathlib import Path
from model import run_diarization
from utils import find_audio_files

def process_path(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    audio_files = find_audio_files(input_path)
    if not audio_files:
        print(f"Путь {input_path} не существует или нет аудио файлов")
        return

    print(f"Найдено {len(audio_files)} файлов для обработки")

    for audio_file in audio_files:
        run_diarization(audio_file, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Diarization Runner")
    parser.add_argument("--input", required=True, help="Файл или папка для обработки")
    parser.add_argument("--output", required=True, help="Папка для сохранения результата")
    args = parser.parse_args()

    process_path(args.input, args.output)




# Для одного файла
# python services/diarization/main.py --input audio/sound/file.wav --output audio/temp_folder


# Для всей папки
# python services/diarization/main.py --input audio/sound --output audio/sound