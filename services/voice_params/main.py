import os
import csv
import argparse
from pathlib import Path  # добавим для красоты
from pipeline import VoiceParamsPipeline
from hash_generator import FileHasher
from file_utils import find_role_files_recursive  # импортируем новую функцию
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


def parse_args():
    parser = argparse.ArgumentParser("Voice params service")
    parser.add_argument("--input", required=True,
                        help="Путь к папке, содержащей *_user.wav и *_assistant.wav (рекурсивно)")
    parser.add_argument("--output", required=True,
                        help="Папка для сохранения CSV документа")
    return parser.parse_args()


def parse_filename(audio_path):
    """
    Извлекает call_id и role из имени файла.
    Ожидается формат: <call_id>_<role>.wav, role = 'assistant' или 'user'.
    """
    filename = os.path.basename(audio_path)
    name, _ = os.path.splitext(filename)
    *parts, role = name.split('_')
    if not parts or role not in ('assistant', 'user'):
        raise ValueError(f"Неверный формат имени файла: {filename}")
    call_id = '_'.join(parts)
    return call_id, role


def extract_features_from_file(audio_path):
    call_id, role = parse_filename(audio_path)
    pipeline = VoiceParamsPipeline(audio_path)
    features = pipeline.run()
    features["call_id"] = call_id
    features["role"] = role
    return features


def process_files(file_list, output_csv, hasher=None):
    rows = []
    for fpath in file_list:
        print(f"Обработка: {fpath}")
        features = extract_features_from_file(fpath)
        if hasher:
            original_id = features["call_id"]
            hashed_id = hasher.hash_name(original_id)
            features["call_id"] = hashed_id
        rows.append(features)

    if not rows:
        print("Нет данных для записи.")
        return

    fieldnames = ["call_id", "role"] + [
        key for key in rows[0].keys()
        if key not in ("call_id", "role")
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Results saved to {output_csv}")


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    hasher = FileHasher(json_path=os.path.join(args.output, "hash_mapping.json"))

    # --- НОВЫЙ КОД: рекурсивный поиск ---
    user_files, assistant_files = find_role_files_recursive(args.input)
    all_files = user_files + assistant_files

    if not all_files:
        print(f"Файлы *_user.wav или *_assistant.wav не найдены в {args.input} (включая подпапки)")
        return

    output_csv = os.path.join(args.output, "features.csv")
    process_files(all_files, output_csv, hasher=hasher)

    hasher.save_json()


if __name__ == "__main__":
    main()


# Для одного файла
# python services/voice_params/main.py --input audio/sound/file.wav --output audio/temp_folder


# Для всей папки
# python services/voice_params/main.py --input audio/sound --output audio/sound