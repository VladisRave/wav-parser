import os
import librosa
import argparse
import numpy as np
import soundfile as sf
from tqdm import tqdm
from typing import List, Tuple

from music_detector import get_music_intervals

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


def parse_args():
    parser = argparse.ArgumentParser(
        "Music removal using YAMNet (нейронная сеть)"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Файл или папка с аудио"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Папка для сохранения результата"
    )

    parser.add_argument(
        "--pre_music_sec",
        type=float,
        default=4.0,
        help="Добавляемая тишина перед музыкой (сек)"
    )

    parser.add_argument(
        "--first_pre_sec",
        type=float,
        default=19.0,
        help="Тишина перед первым музыкальным фрагментом"
    )

    parser.add_argument(
        "--silence_duration",
        type=float,
        default=0.5,
        help="Длительность вставляемой тишины"
    )

    parser.add_argument(
        "--music_threshold",
        type=float,
        default=0.6,
        help="Порог вероятности музыки (0.0–1.0)"
    )

    parser.add_argument(
        "--merge_gap",
        type=float,
        default=1.0,
        help="Объединение близких музыкальных сегментов (сек)"
    )

    parser.add_argument(
        "--min_audio_len",
        type=float,
        default=20.0,
        help="Минимальная длина аудио для обработки"
    )

    return parser.parse_args()


def get_audio_files(input_path: str) -> List[str]:
    """
    Получает список аудиофайлов для обработки.

    Args:
        input_path: путь к файлу или папке

    Returns:
        список файлов
    """
    if os.path.isfile(input_path):
        return [input_path]

    if os.path.isdir(input_path):
        exts = (".mp3", ".wav", ".flac", ".ogg", ".m4a")

        return [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(exts)
        ]

    raise FileNotFoundError(f"Не найден путь: {input_path}")


def replace_music_with_silence(
    y_full: np.ndarray,
    sr: int,
    intervals_sec: List[Tuple[float, float]],
    output_path: str,
    pre_music_sec: float,
    first_pre_sec: float,
    silence_duration: float
) -> np.ndarray:
    """
    Заменяет музыкальные участки тишиной.

    Args:
        y_full: аудиосигнал
        sr: sample rate
        intervals_sec: интервалы музыки
        output_path: путь сохранения
        pre_music_sec: запас перед сегментом
        first_pre_sec: запас перед первым сегментом
        silence_duration: длительность тишины

    Returns:
        обработанный сигнал
    """

    result = []
    cursor = 0

    silence = np.zeros(int(sr * silence_duration), dtype=y_full.dtype)

    for i, (start_sec, end_sec) in enumerate(intervals_sec):

        pad = first_pre_sec if i == 0 else pre_music_sec

        start = max(0, int(start_sec * sr) - int(pad * sr))
        end = min(len(y_full), int(end_sec * sr))

        if cursor < start:
            result.append(y_full[cursor:start])

        result.append(silence)
        cursor = end

    if cursor < len(y_full):
        result.append(y_full[cursor:])

    y_out = np.concatenate(result)

    sf.write(output_path, y_out, sr)

    return y_out


def main() -> None:
    """
    Главный pipeline удаления музыки.
    """

    args = parse_args()

    os.makedirs(args.output, exist_ok=True)

    files = get_audio_files(args.input)

    if not files:
        print("Файлы не найдены")
        return

    for file_path in tqdm(files, desc="Music removal"):

        print(f"\nОбработка: {file_path}")

        try:
            y_full, sr = librosa.load(file_path, sr=None, mono=True)

        except Exception as error:
            print(f"Ошибка загрузки {file_path}: {error}")
            continue

        duration = len(y_full) / sr

        if duration <= args.min_audio_len:
            print(
                f"Пропуск (длина {duration:.2f} сек < "
                f"{args.min_audio_len} сек)"
            )
            continue

        intervals = get_music_intervals(
            file_path,
            music_threshold=args.music_threshold,
            merge_gap_sec=args.merge_gap
        )

        print(f"Найдено музыкальных блоков: {len(intervals)}")

        base_name = os.path.splitext(os.path.basename(file_path))[0]

        file_output_dir = os.path.join(args.output, base_name)
        os.makedirs(file_output_dir, exist_ok=True)

        output_file = os.path.join(file_output_dir, f"{base_name}.wav")

        if intervals:
            replace_music_with_silence(
                y_full,
                sr,
                intervals,
                output_file,
                args.pre_music_sec,
                args.first_pre_sec,
                args.silence_duration
            )

            print(f"Музыка удалена: {output_file}")

        else:
            sf.write(output_file, y_full, sr)
            print(f"Музыка не найдена: {output_file}")


if __name__ == "__main__":
    main()


# ==============================
# Примеры запуска
# ==============================

# Для одного файла
# python services/music_removal/main.py \
# --input /path/to/file.mp3 \
# --output /path/to/output_folder


# Для всей папки
# python services/music_removal/main.py \
# --input /path/to/input_folder \
# --output /path/to/output_folder