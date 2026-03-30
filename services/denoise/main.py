from pathlib import Path
import argparse
import os
from tqdm import tqdm
from denoise import process_audio, save_audio

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


def parse_args():
    parser = argparse.ArgumentParser("Denoise service")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target_db", type=float, default=-28)
    parser.add_argument("--max_gain_db", type=float, default=6)
    parser.add_argument("--hpf_cutoff", type=float, default=70)
    return parser.parse_args()


def get_audio_files(input_path):
    input_path = Path(input_path)

    if input_path.is_file():
        return [input_path]

    elif input_path.is_dir():
        exts = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
        skip_dirs = {"input"}
        return [
            p for p in input_path.rglob("*")
            if p.suffix.lower() in exts
            and not any(part in skip_dirs for part in p.relative_to(input_path).parts)
        ]

    else:
        raise FileNotFoundError(f"Путь не найден: {input_path}")


def main():
    args = parse_args()

    input_root = Path(args.input).resolve()
    output_root = Path(args.output).resolve()

    output_root.mkdir(parents=True, exist_ok=True)

    files = get_audio_files(input_root)

    if not files:
        print("Файлы не найдены")
        return

    print(f"Найдено файлов: {len(files)}")

    for file_path in tqdm(files, desc="Denoise"):
        try:
            file_path = Path(file_path)

            # ==============================
            # СОХРАНЯЕМ СТРУКТУРУ ПАПОК
            # ==============================
            relative_dir = file_path.parent.relative_to(input_root)

            # создаём такую же структуру в output
            out_dir = output_root / relative_dir
            out_dir.mkdir(parents=True, exist_ok=True)

            # имя файла
            output_path = out_dir / f"{file_path.stem}.wav"

            print(f"Обработка: {file_path} -> {output_path}")

            y, sr = process_audio(
                str(file_path),
                target_db=args.target_db,
                max_gain_db=args.max_gain_db,
                hpf_cutoff=args.hpf_cutoff
            )

            save_audio(y, sr, str(output_path))

        except Exception as e:
            print(f"Ошибка при обработке {file_path}: {e}")


if __name__ == "__main__":
    main()

# Для одного файла
# python services/denoise/main.py --input /home/user/wav-parser/audio/sound/sozvon.mp3 --output /home/user/wav-parser/audio/AAA


# Для всей папки
# python services/denoise/main.py --input /home/user/wav-parser/audio/tracks --output /home/user/wav-parser/audio/trracks