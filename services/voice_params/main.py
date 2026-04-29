import os
import csv
import argparse
import parselmouth
import numpy as np
from tqdm import tqdm
from pathlib import Path
from typing import List, Dict

from feature_extractor import extract_features 
from file_utils import find_role_files_recursive
from gender_control import get_gender   # <-- импортируем функцию

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Voice params service")
    parser.add_argument(
        "--input",
        required=True,
        help="Папка с *_user.wav и *_assistant.wav",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Папка для сохранения CSV",
    )
    parser.add_argument(
        "--mode",
        choices=["user", "assistant", "both"],
        default="both",
        help="Какие файлы обрабатывать",
    )
    return parser.parse_args()


def load_sound(audio_path: Path) -> parselmouth.Sound:
    sound = parselmouth.Sound(str(audio_path))
    y = sound.values.T.flatten()
    sr = sound.sampling_frequency
    y = np.nan_to_num(y)
    return parselmouth.Sound(y, sampling_frequency=sr)


def parse_filename(audio_path: Path) -> tuple[str, str]:
    name = audio_path.stem
    parts = name.split("_")
    if len(parts) < 2:
        raise ValueError(f"Неверное имя файла: {audio_path.name}")
    role = parts[-1]
    call_id = "_".join(parts[:-1])
    return call_id, role


def extract_features_from_file(audio_path: Path) -> Dict:
    sound = load_sound(audio_path)
    features = extract_features(sound)
    call_id, role = parse_filename(audio_path)
    features["call_id"] = call_id
    features["role"] = role
    return features


def process_files(file_list: List[Path], output_csv: str) -> None:
    rows = []
    for fpath in tqdm(file_list, desc="Voice params"):
        print(f"Обработка: {fpath}")
        try:
            features = extract_features_from_file(fpath)
            gender = get_gender(str(fpath))
            row = {**features, "defined_gender": gender}
            rows.append(row)
        except Exception as e:
            print(f"Ошибка в {fpath}: {e}")
            continue

    if not rows:
        print("Нет данных для записи.")
        return

    fieldnames = ["call_id", "role", "defined_gender"] + [
        k for k in rows[0].keys() 
        if k not in ("call_id", "role", "defined_gender")
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Results saved to {output_csv}")


def main() -> None:
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    include_user = args.mode in ("user", "both")
    include_assistant = args.mode in ("assistant", "both")

    user_files, assistant_files = find_role_files_recursive(args.input)

    all_files = []
    if include_user:
        all_files.extend(user_files)
    if include_assistant:
        all_files.extend(assistant_files)

    if not all_files:
        print(f"Файлы не найдены в {args.input}")
        return

    output_csv = os.path.join(args.output, "features.csv")
    process_files(all_files, output_csv)


if __name__ == "__main__":
    main()


# ==============================
# Примеры запуска
# ==============================

# Для одного файла
# python services/voice_params/main.py \
# --input /path/to/file.mp3 \
# --output /path/to/output_folder


# Для всей папки
# python services/voice_params/main.py \
# --input /path/to/input_folder \
# --output /path/to/output_folder