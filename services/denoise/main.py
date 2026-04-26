import argparse
import warnings
from pathlib import Path
from typing import List

from tqdm import tqdm

from denoise import process_audio, save_audio


warnings.filterwarnings("ignore", category=UserWarning)


AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
SKIP_DIRS = {"input"}


def parse_args():
    parser = argparse.ArgumentParser("Denoise service")

    parser.add_argument(
        "--input",
        required=True,
        help="Файл или папка с аудио",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Папка для сохранения результата",
    )

    parser.add_argument(
        "--target_db",
        type=float,
        default=-28,
        help="Целевая громкость (dB)",
    )

    parser.add_argument(
        "--max_gain_db",
        type=float,
        default=6,
        help="Максимальное усиление (dB)",
    )

    parser.add_argument(
        "--hpf_cutoff",
        type=float,
        default=70,
        help="Частота high-pass фильтра",
    )

    return parser.parse_args()


def get_audio_files(input_path: Path) -> List[Path]:
    """
    Получает список аудиофайлов.

    Поддерживает:
        - Один файл
        - Папку с файлами
        - Рекурсивный поиск

    Args:
        input_path: Путь к файлу или папке

    Returns:
        Список аудиофайлов
    """

    input_path = Path(input_path)

    if input_path.is_file():
        return [input_path]

    if input_path.is_dir():
        return [
            path
            for path in input_path.rglob("*")
            if path.suffix.lower() in AUDIO_EXTENSIONS
            and not any(
                part in SKIP_DIRS
                for part in path.relative_to(input_path).parts
            )
        ]

    raise FileNotFoundError(f"Путь не найден: {input_path}")


def main() -> None:
    """
    Основная функция обработки аудио.
    """

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
            relative_dir = file_path.parent.relative_to(input_root)

            out_dir = output_root / relative_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / f"{file_path.stem}.wav"

            print(f"Обработка: {file_path} -> {output_path}")

            # Обработка аудио
            y, sr = process_audio(
                str(file_path),
                target_db=args.target_db,
                max_gain_db=args.max_gain_db,
                hpf_cutoff=args.hpf_cutoff,
            )

            # Сохранение результата
            save_audio(y, sr, str(output_path))

        except Exception as error:
            print(
                f"Ошибка при обработке {file_path}: {error}"
            )


if __name__ == "__main__":
    main()


# ==============================
# Примеры запуска
# ==============================

# Для одного файла
# python services/denoise/main.py \
# --input /path/to/file.mp3 \
# --output /path/to/output_folder


# Для всей папки
# python services/denoise/main.py \
# --input /path/to/input_folder \
# --output /path/to/output_folder