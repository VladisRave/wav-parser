import argparse
from pathlib import Path

import torch
from tqdm import tqdm
from detect_roles import detect_roles

TEXT_EXTENSIONS = [".txt"]  # форматы расшифровок


def process_single_file(input_file: Path, output_file: Path):
    """
    Читает один файл расшифровки, вызывает LLM и записывает JSON.
    """
    text = input_file.read_text(encoding="utf-8")
    roles_json = detect_roles(text)  # получаем JSON от LLM

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(roles_json)

    print(f"Роли сохранены: {output_file}")


def main():
    parser = argparse.ArgumentParser("Speaker Role Marker")
    parser.add_argument("--input", required=True, help="Файл или папка с расшифровками")
    parser.add_argument("--output", required=False, help="Папка для сохранения JSON (если не указана, сохраняет рядом с исходными файлами)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else None

    # --- Обработка случая, когда входной путь — файл ---
    if input_path.is_file():
        if not any(input_path.suffix == ext for ext in TEXT_EXTENSIONS):
            print(f"Файл {input_path} не является поддерживаемым расшифровкой (расширение не в {TEXT_EXTENSIONS})")
            return

        if output_path:
            # Если указана выходная папка — создаём её и сохраняем файл туда
            output_path.mkdir(parents=True, exist_ok=True)
            out_file = output_path / f"{input_path.stem}_roles.json"
        else:
            # Сохраняем рядом с исходным файлом
            out_file = input_path.with_name(f"{input_path.stem}_roles.json")

        process_single_file(input_path, out_file)

    # --- Обработка случая, когда входной путь — папка ---
    elif input_path.is_dir():
        # Собираем все файлы с нужными расширениями рекурсивно
        files = []
        for ext in TEXT_EXTENSIONS:
            files.extend(input_path.rglob(f"*{ext}"))

        if not files:
            print("Файлы расшифровок не найдены")
            return

        print(f"Найдено {len(files)} файлов для обработки")

        for file_path in tqdm(files, desc="Role parsing"):
            if output_path:
                # Сохраняем с сохранением структуры папок относительно input_path
                relative_dir = file_path.parent.relative_to(input_path)
                out_dir = output_path / relative_dir
                out_file = out_dir / f"{file_path.stem}_roles.json"
            else:
                # Сохраняем рядом с файлом
                out_file = file_path.with_name(f"{file_path.stem}_roles.json")

            try:
                process_single_file(file_path, out_file)
            except torch.cuda.OutOfMemoryError:
                print(f"\nOOM on {file_path.name}, skipping")
                torch.cuda.empty_cache()

    else:
        print(f"Указанный путь не существует: {input_path}")


if __name__ == "__main__":
    main()



# Для одного файла
# python services/role_parser/main.py --input audio/sound/file.wav --output audio/temp_folder


# Для всей папки
# python services/role_parser/main.py --input audio/tracks --output audio/tracks