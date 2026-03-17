import argparse
import os
from denoise import process_audio, save_audio

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


def parse_args():
    parser = argparse.ArgumentParser("Denoise service")
    parser.add_argument("--input", required=True, help="Путь к файлу или папке с аудио")
    parser.add_argument("--output", required=True, help="Корневая папка для сохранения результатов")
    parser.add_argument("--target_db", type=float, default=-28, help="Целевой уровень RMS (дБ)")
    parser.add_argument("--max_gain_db", type=float, default=6, help="Максимальное усиление фрейма (дБ)")
    parser.add_argument("--hpf_cutoff", type=float, default=70, help="Частота среза HPF (Гц)")
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
        # Создаём папку с именем файла внутри выходной директории
        file_out_dir = os.path.join(args.output, base)
        os.makedirs(file_out_dir, exist_ok=True)
        output_path = os.path.join(file_out_dir, f"{base}.wav")

        print(f"Обработка: {file_path} -> {output_path}")

        try:
            y, sr = process_audio(
                file_path,
                target_db=args.target_db,
                max_gain_db=args.max_gain_db,
                hpf_cutoff=args.hpf_cutoff
            )
            save_audio(y, sr, output_path)
        except Exception as e:
            print(f"Ошибка при обработке {file_path}: {e}")


if __name__ == "__main__":
    main()


# Для одного файла
# python services/denoise/main.py --input /home/user/wav-parser/audio/sound/sozvon.mp3 --output /home/user/wav-parser/audio/AAA


# Для всей папки
# python services/denoise/main.py --input /home/user/wav-parser/audio/sound --output /home/user/wav-parser/audio/sound