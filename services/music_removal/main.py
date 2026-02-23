# main.py
import argparse
import os
import librosa
import soundfile as sf

from music_search import (
    extract_chroma_features,
    coarse_music_search,
    refine_music_search,
    merge_time_intervals,
    replace_music_with_silence
)

import warnings
warnings.filterwarnings("ignore", category=UserWarning)


def parse_args():
    p = argparse.ArgumentParser("Music removal service")
    p.add_argument(
        "--input", required=True,
        help="Путь к исходному аудиофайлу (mp3/wav) или папке с файлами для обработки"
    )
    p.add_argument(
        "--music_dir", required=True,
        help="Папка с WAV файлами музыкальных фрагментов, которые нужно удалить"
    )
    p.add_argument(
        "--output", required=True,
        help="Папка для сохранения обработанных файлов"
    )
    p.add_argument(
        "--pre_music_sec", type=float, default=2.0,
        help="Секунды до музыкального фрагмента, которые тоже заменяются тишиной"
    )
    p.add_argument(
        "--silence_duration", type=float, default=3.0,
        help="Длительность тишины, вставляемой вместо музыки (в секундах)"
    )
    return p.parse_args()


def get_audio_files(input_path):
    """Возвращает список файлов для обработки"""
    if os.path.isfile(input_path):
        return [input_path]
    elif os.path.isdir(input_path):
        exts = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
        return [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(exts)
        ]
    else:
        raise FileNotFoundError(f"Не найден файл или папка: {input_path}")


def main():
    args = parse_args()

    # Создаём выходную папку
    os.makedirs(args.output, exist_ok=True)

    # Получаем список файлов для обработки
    files_to_process = get_audio_files(args.input)
    if not files_to_process:
        print("Не найдено аудиофайлов для обработки.")
        return

    # Получаем список музыкальных WAV для удаления
    music_files = [
        os.path.join(args.music_dir, f)
        for f in os.listdir(args.music_dir)
        if f.lower().endswith(".wav")
    ]
    if not music_files:
        print("Не найдено WAV файлов с музыкой для удаления.")
        return

    for file_path in files_to_process:
        print(f"\nОбработка: {file_path}")
        try:
            y_full, sr = librosa.load(file_path, sr=None, mono=True)
        except Exception as e:
            print(f"Ошибка загрузки {file_path}: {e}")
            continue

        win_sec = 3.0
        overlap = 0.33
        win_len = int(sr * win_sec)
        step_len = int(sr * win_sec * (1 - overlap))

        all_intervals = []

        for fname in music_files:
            try:
                y_music, _ = librosa.load(fname, sr=sr, mono=True)
            except Exception as e:
                print(f"Ошибка загрузки {fname}: {e}")
                continue

            if len(y_music) < win_len:
                print(f"Пропускаем {fname}, слишком короткий (<{win_sec} сек)")
                continue

            y_ref = y_music[:win_len]
            chroma_ref = extract_chroma_features(y_ref, sr)

            candidates = coarse_music_search(
                y_full=y_full,
                win_len=win_len,
                chroma_reference=chroma_ref,
                step_len=step_len,
                sr=sr
            )

            refined = refine_music_search(
                y_full=y_full,
                y_reference=y_music,
                candidates=candidates,
                win_len=win_len,
                sr=sr
            )

            for start, end in refined:
                start_sec = max(0.0, start / sr - args.pre_music_sec)
                all_intervals.append((start_sec, end / sr))

        merged = merge_time_intervals(all_intervals)
        print(f"Всего найдено музыкальных блоков: {len(merged)}")

        # Имя файла без пути и расширения
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # ЕСЛИ МУЗЫКА НАЙДЕНА
        if merged:
            output_file = os.path.join(args.output, f"{base_name}_clean.wav")

            replace_music_with_silence(
                y_full=y_full,
                sr=sr,
                intervals_sec=merged,
                output_path=output_file,
                pre_music_sec=args.pre_music_sec,
                silence_duration=args.silence_duration
            )

            print(f"Музыка найдена. Файл сохранён как: {output_file}")

        # ЕСЛИ МУЗЫКИ НЕТ
        else:
            output_file = os.path.join(args.output, f"{base_name}.wav")
            sf.write(output_file, y_full, sr)

            print(f"Музыка не найдена. Файл сохранён как: {output_file}")


if __name__ == "__main__":
    main()


# Код для запуска обработки одного трека
# python ./services/music_removal/main.py --input /home/user/WAV-Parser/audio/tracks/file.wav \
# --music_dir /home/user/WAV-Parser/audio/clips/ \
# --output /home/user/WAV-Parser/audio/clean_audio

# Код для запуска обработки папки
# python ./services/music_removal/main.py --input /home/user/wav-parser/audio/tracks/ \
# --music_dir /home/user/wav-parser/audio/clips/ \
# --output /home/user/wav-parser/audio/clean_audio