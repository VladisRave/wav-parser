# main.py
import os
import csv
import argparse
from pipeline import VoiceParamsPipeline
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ====== Импортируем хэширование файлов ======
from hash_gen import FileHasher

def parse_args():
    parser = argparse.ArgumentParser("Voice params service")
    parser.add_argument(
        "--input", required=True, help="Путь к аудио файлу или папке с файлами"
    )
    parser.add_argument(
        "--output", required=True, help="Папка для сохранения CSV документа"
    )
    return parser.parse_args()


def parse_filename(audio_path):
    """
    Извлекает call_id и role из имени файла.
    Пример: 52_operator.wav -> (52, operator)
    """
    filename = os.path.basename(audio_path)
    name, _ = os.path.splitext(filename)
    parts = name.split("_")
    if len(parts) < 2:
        raise ValueError(f"Неверный формат имени файла: {filename}")
    call_id = parts[0]
    role = parts[1]
    return call_id, role


def extract_features_from_file(audio_path):
    """
    Обрабатывает один .wav файл через пайплайн
    и возвращает словарь с признаками + call_id + role.
    """
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

        # Если есть хэшер — меняем call_id на хэш
        if hasher:
            original_id = features["call_id"]
            hashed_id = hasher.hash_name(original_id)
            features["call_id"] = hashed_id

        rows.append(features)

    if not rows:
        print("Нет данных для записи.")
        return

    # фиксируем порядок колонок: сначала call_id и role
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

    # Создаём хэшер
    hasher = FileHasher(json_path=os.path.join(args.output, "hash_mapping.json"))

    # Получаем список файлов
    if os.path.isdir(args.input):
        files = [
            os.path.join(args.input, f)
            for f in os.listdir(args.input)
            if f.lower().endswith(".wav")
        ]
        if not files:
            print(f"Файлы .wav не найдены в {args.input}")
            return
        output_csv = os.path.join(args.output, "features.csv")
        process_files(files, output_csv, hasher=hasher)

    elif os.path.isfile(args.input):
        if not args.input.lower().endswith(".wav"):
            print("Указанный файл не является .wav")
            return
        output_csv = os.path.join(args.output, "features.csv")
        process_files([args.input], output_csv, hasher=hasher)

    else:
        print(f"Указанный путь не существует: {args.input}")
        return

    # Сохраняем JSON с хэшами
    hasher.save_json()


if __name__ == "__main__":
    main()


# python ./services/voice_params/main.py --input /home/user/wav-parser/audio/result/ \
# --output /home/user/wav-parser/audio/result