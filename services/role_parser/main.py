import json
import torch
import argparse
from tqdm import tqdm
from pathlib import Path

from detect_roles import detect_roles, extract_user_text, quality_control, save_roles, validate_operator_user

TEXT_EXTENSIONS = [".txt"]


def process_single_file(input_file: Path, output_file: Path) -> None:
    text = input_file.read_text(encoding="utf-8")

    roles_dict = detect_roles(text)

    if not roles_dict:
        print(f"  Ошибка: роли не определены в {input_file.name}")
        return

    user_speaker = None
    assistant_speaker = None

    for speaker, role in roles_dict.items():
        if role == "USER":
            user_speaker = speaker
        elif role == "ASSISTANT":
            assistant_speaker = speaker

    if user_speaker and assistant_speaker:
        is_roles_ok = validate_operator_user(text, roles_dict)

        if not is_roles_ok:
            print(f"  QC1 FAIL: роли некорректны → удаляем USER и ASSISTANT")

            del roles_dict[user_speaker]
            del roles_dict[assistant_speaker]

            # сохраняем и выходим
            save_roles(output_file, roles_dict)
            return
        else:
            print(f"  QC1 PASS: роли корректны")

    else:
        print("  QC1 SKIP: нет пары USER + ASSISTANT")

    if user_speaker and user_speaker in roles_dict:
        user_text = extract_user_text(text, user_speaker)

        if user_text:
            is_good = quality_control(user_text)

            if not is_good:
                print(f"  QC2 FAIL: USER удалён ({user_speaker})")
                del roles_dict[user_speaker]
            else:
                print(f"  QC2 PASS: USER оставлен ({user_speaker})")
        else:
            print(f"  ВНИМАНИЕ: нет текста USER")

    save_roles(output_file, roles_dict)


def main() -> None:
    """Точка входа в систему определения ролей спикеров с контролем качества."""
    parser = argparse.ArgumentParser(
        description="Speaker Role Marker with Quality Control"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Файл или папка с расшифровками",
    )
    parser.add_argument(
        "--output",
        required=False,
        help=(
            "Папка для сохранения JSON. "
            "Если не указана — сохраняется рядом с исходными файлами"
        ),
    )

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else None

    # Обработка одного файла
    if input_path.is_file():
        if input_path.suffix not in TEXT_EXTENSIONS:
            print(
                f"Файл {input_path} не поддерживается "
                f"(разрешены: {TEXT_EXTENSIONS})"
            )
            return

        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
            out_file = output_path / f"{input_path.stem}_roles.json"
        else:
            out_file = input_path.with_name(f"{input_path.stem}_roles.json")

        process_single_file(input_path, out_file)

    # Обработка директории
    elif input_path.is_dir():
        files = []
        for ext in TEXT_EXTENSIONS:
            files.extend(input_path.rglob(f"*{ext}"))

        if not files:
            print("Файлы расшифровок не найдены")
            return

        print(f"Найдено {len(files)} файлов для обработки")

        for file_path in tqdm(files, desc="Role parsing + QC"):
            if output_path:
                relative_dir = file_path.parent.relative_to(input_path)
                out_dir = output_path / relative_dir
                out_file = out_dir / f"{file_path.stem}_roles.json"
            else:
                out_file = file_path.with_name(f"{file_path.stem}_roles.json")

            try:
                process_single_file(file_path, out_file)
            except torch.cuda.OutOfMemoryError:
                print(f"\nOOM на {file_path.name}, пропускаем")
                torch.cuda.empty_cache()
            except Exception as e:
                print(f"\nОшибка при обработке {file_path.name}: {e}")

    else:
        print(f"Указанный путь не существует: {input_path}")


if __name__ == "__main__":
    main()


# ==============================
# Примеры запуска
# ==============================

# Для одного файла
# python services/role_parser/main.py \
# --input /path/to/file.mp3 \
# --output /path/to/output_folder


# Для всей папки
# python services/role_parser/main.py \
# --input /path/to/input_folder \
# --output /path/to/output_folder