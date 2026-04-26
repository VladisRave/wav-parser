import argparse
from pathlib import Path

from tqdm import tqdm

from splitter import split_audio_by_role


def main() -> None:
    """
    CLI для разбиения аудио по ролям спикеров.

    Args:
        нет

    Input:
        --input_dir: директория с аудио, SRT и JSON
        --output_dir: директория для сохранения результата
        --roles: список ролей для выгрузки (USER, ASSISTANT, ROBOT)

    Output:
        набор .wav файлов, разделённых по выбранным ролям

    Result:
        - рекурсивно ищет аудиофайлы
        - проверяет наличие SRT и JSON
        - фильтрует роли по пользовательскому выбору
        - сохраняет аудио только для выбранных ролей
    """
    parser = argparse.ArgumentParser(
        "Split audio by roles from SRT and JSON"
    )

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Папка с аудио, SRT и JSON (рекурсивно)",
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Папка для сохранения результатов",
    )

    parser.add_argument(
        "--roles",
        required=False,
        default="USER,ASSISTANT,ROBOT",
        help=(
            "Роли для выгрузки через запятую. "
            "Пример: USER,ROBOT или ASSISTANT"
        ),
    )

    args = parser.parse_args()

    input_root = Path(args.input_dir).resolve()
    output_root = Path(args.output_dir).resolve()
    selected_roles = {role.strip().upper() for role in args.roles.split(",") if role.strip()}

    wav_files = list(input_root.rglob("*.wav"))
    if not wav_files:
        print(f"Нет .wav файлов в {input_root}")
        return

    for wav_path in tqdm(wav_files, desc="Audio separation"):
        src_dir = wav_path.parent
        base_name = wav_path.stem

        srt_path = src_dir / f"{base_name}.srt"
        json_path = src_dir / f"{base_name}_roles.json"

        if not srt_path.exists() or not json_path.exists():
            print(f"Пропускаем {wav_path}: нет SRT или JSON")
            continue

        # Проверяем содержимое JSON
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                roles_dict = json.load(f)
            if not roles_dict:
                print(f"Пропускаем {wav_path}: JSON пустой")
                continue
            # Если нужны USER или ASSISTANT – проверяем их наличие
            if "USER" in selected_roles and "USER" not in roles_dict.values():
                print(f"Пропускаем {wav_path}: нет USER в JSON")
                continue
            if "ASSISTANT" in selected_roles and "ASSISTANT" not in roles_dict.values():
                print(f"Пропускаем {wav_path}: нет ASSISTANT в JSON")
                continue
        except Exception as e:
            print(f"Пропускаем {wav_path}: ошибка чтения JSON - {e}")
            continue

        rel_path = src_dir.relative_to(input_root)
        target_dir = output_root / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"Обработка {base_name}...")
        split_audio_by_role(
            wav_path,
            srt_path,
            json_path,
            target_dir,
            selected_roles=selected_roles,
        )


if __name__ == "__main__":
    main()


# ==============================
# Примеры запуска
# ==============================

# Для одного файла
# python services/audio_separation/main.py \
# --input /path/to/file.mp3 \
# --output /path/to/output_folder


# Для всей папки
# python services/audio_separation/main.py \
# --input /path/to/input_folder \
# --output /path/to/output_folder