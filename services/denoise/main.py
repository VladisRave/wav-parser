import argparse
import os
from denoise import process_audio, save_audio

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


def parse_args():
    parser = argparse.ArgumentParser("Denoise service")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()

def get_audio_files(input_path):
    if os.path.isfile(input_path):
        return [input_path]
    elif os.path.isdir(input_path):
        exts = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
        return [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(exts)
        ]
    else:
        raise FileNotFoundError(f"Путь не найден: {input_path}")

def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    files = get_audio_files(args.input)
    if not files:
        print("Файлы не найдены")
        return

    for file_path in files:
        base = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(args.output, f"{base}_filt.wav")

        print(f"Processing: {file_path}")

        try:
            y, sr = process_audio(file_path)
            save_audio(y, sr, output_path)

        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()


# Для одного файла
# python ./services/denoise/main.py --input /home/user/wav-parser/audio/clean_audio/file.wav --output /home/user/wav-parser/audio/filt_audio

# Для всей папки
# python ./services/denoise/main.py --input /home/user/wav-parser/audio/clean_audio/ --output /home/user/wav-parser/audio/filt_audio