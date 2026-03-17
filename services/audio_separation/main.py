import argparse
from pathlib import Path

from splitter import split_audio_by_role


def main():
    parser = argparse.ArgumentParser("Split audio by roles from SRT and JSON")
    parser.add_argument("--input_dir", required=True, help="Папка, содержащая .wav, .srt, .json файлы (рекурсивно)")
    parser.add_argument("--output_dir", required=True, help="Папка для сохранения результирующих .wav файлов по ролям (структура подпапок сохранится)")
    parser.add_argument("--normalize", action="store_true", help="Применить нормализацию громкости к выходным файлам")
    parser.add_argument("--target_db", type=float, default=-28, help="Целевой уровень громкости в dBFS (если normalize)")
    args = parser.parse_args()

    input_root = Path(args.input_dir).resolve()
    output_root = Path(args.output_dir).resolve()

    # Рекурсивно ищем все .wav файлы
    wav_files = list(input_root.rglob("*.wav"))
    if not wav_files:
        print(f"Нет .wav файлов в {input_root} (включая подпапки)")
        return

    for wav_path in wav_files:
        # Определяем папку, где лежит wav
        src_dir = wav_path.parent
        base_name = wav_path.stem

        # Ищем соответствующие .srt и .json в той же папке
        srt_path = src_dir / f"{base_name}.srt"
        json_path = src_dir / f"{base_name}_roles.json"

        if not (srt_path.exists() and json_path.exists()):
            print(f"Пропускаем {wav_path}: отсутствует .srt или .json")
            continue

        # Вычисляем относительный путь от input_root до папки с файлом
        rel_path = src_dir.relative_to(input_root)
        # Создаём целевую папку внутри output_root с тем же относительным путём
        target_dir = output_root / rel_path
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"Обработка {base_name} в {src_dir}...")
        split_audio_by_role(
            wav_path, srt_path, json_path,
            target_dir,                     # сохраняем в соответствующую подпапку
            normalize=args.normalize,
            target_db=args.target_db
        )


if __name__ == "__main__":
    main()


# Для одного файла
# python services/audio_separation/main.py --input audio/sound/file.wav --output audio/temp_folder


# Для всей папки
# python services/audio_separation/main.py --input audio/sound --output audio/sound