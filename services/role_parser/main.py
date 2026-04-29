import re
import asyncio
import argparse

from pathlib import Path

from detect_roles import detect_roles, extract_user_text, validate_combined, save_roles
from llm import token_stats, LLM_MODE

TEXT_EXTENSIONS = [".txt"]
MAX_CONCURRENT = 5

async def process_single_file(input_file: Path, output_file: Path, semaphore: asyncio.Semaphore):
    async with semaphore:
        text = input_file.read_text(encoding="utf-8")
        if len(text) < 200:
            print(f"  Пропуск (слишком короткий): {input_file.name}")
            return
        speakers = set(re.findall(r"^(Speaker \d+):", text, re.MULTILINE))
        if len(speakers) < 2:
            print(f"  Пропуск (меньше 2 спикеров): {input_file.name}")
            return

        roles_dict = await detect_roles(text)
        if not roles_dict:
            print(f"  Роли не определены: {input_file.name}")
            return

        user_speaker = next((s for s, r in roles_dict.items() if r == "USER"), None)
        assistant_speaker = next((s for s, r in roles_dict.items() if r == "ASSISTANT"), None)

        if not user_speaker or not assistant_speaker:
            save_roles(output_file, roles_dict)
            return

        user_text = extract_user_text(text, user_speaker)
        roles_valid, quality_ok = await validate_combined(text, roles_dict, user_text)

        if not roles_valid:
            del roles_dict[user_speaker]
            del roles_dict[assistant_speaker]
        elif not quality_ok and user_speaker in roles_dict:
            del roles_dict[user_speaker]

        save_roles(output_file, roles_dict)

async def process_all(files: list, output_base: Path, input_base: Path):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = []
    for file_path in files:
        if output_base:
            relative_dir = file_path.parent.relative_to(input_base)
            out_dir = output_base / relative_dir
            out_file = out_dir / f"{file_path.stem}_roles.json"
        else:
            out_file = file_path.with_name(f"{file_path.stem}_roles.json")
        tasks.append(process_single_file(file_path, out_file, semaphore))
    for coro in asyncio.as_completed(tasks):
        await coro

def main():
    parser = argparse.ArgumentParser(description="Speaker Role Marker with QC")
    parser.add_argument("--input", required=True, help="Файл или папка с расшифровками")
    parser.add_argument("--output", required=False, help="Папка для сохранения JSON")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else None

    if input_path.is_file():
        if input_path.suffix not in TEXT_EXTENSIONS:
            print(f"Неподдерживаемый формат: {input_path}")
            return
        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
            out_file = output_path / f"{input_path.stem}_roles.json"
        else:
            out_file = input_path.with_name(f"{input_path.stem}_roles.json")
        asyncio.run(process_single_file(input_path, out_file, asyncio.Semaphore(1)))
    elif input_path.is_dir():
        files = [p for ext in TEXT_EXTENSIONS for p in input_path.rglob(f"*{ext}")]
        if not files:
            print("Файлы не найдены")
            return
        print(f"Найдено {len(files)} файлов, начинаем асинхронную обработку (макс. {MAX_CONCURRENT} конкурентных запросов)")
        asyncio.run(process_all(files, output_path, input_path))
    else:
        print("Путь не существует")
        return
    stats = token_stats.report()
    print("\n" + "="*50)
    print("СТАТИСТИКА LLM-ВЫЗОВОВ")
    print(f"Всего вызовов: {stats['calls']}")
    print(f"Input tokens (total): {stats['total_input_tokens']}")
    print(f" - cached:            {stats['cached_input_tokens']}")
    print(f" - non-cached:        {stats['non_cached_input_tokens']}")
    print(f"Avg input tokens / call:  {stats['avg_input_tokens_per_call']}")
    print(f"Output tokens: {stats['output_tokens']}")
    print(f"Avg output tokens / call: {stats['avg_output_tokens_per_call']}")
    print(f"Total tokens:  {stats['total_tokens']}")
    if LLM_MODE == "server":
        print(f"Примерная стоимость: {stats['cost']} рублей")
    else:
        print("Локальная модель – стоимость не учитывается.")
    print("="*50)

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