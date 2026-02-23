import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
import warnings

from pipeline import DiarizationPipeline
from audio_writer import write_speaker_audio

warnings.filterwarnings("ignore")


def parse_args():
    p = argparse.ArgumentParser("Diarization service")
    p.add_argument("--input", required=True, help="Путь к аудио файлу или папке")
    p.add_argument("--output", required=True, help="Папка для сохранения результата")
    return p.parse_args()


def extract_numeric_id(file_path):
    base = os.path.basename(file_path)
    stem = os.path.splitext(base)[0]
    return stem.split("_")[0]


def process_file(file_path, output_dir):
    file_id = extract_numeric_id(file_path)
    print(f"\n🔊 Обрабатываем: {file_path}")

    pipeline = DiarizationPipeline(file_path)
    result = pipeline.run()

    speakers = result.get("speakers", [])

    if not speakers:
        print(f"⚠️ Люди не найдены: {file_path}")
        return

    # 🎯 Определение ролей
    roles = {}

    if "clean_filt" in os.path.basename(file_path) and len(speakers) >= 2:
        roles[speakers[0]] = "target"
        roles[speakers[1]] = "operator"
    else:
        roles[speakers[0]] = "target"

    # 💾 Сохраняем
    for spk, role in roles.items():
        final_path = os.path.join(output_dir, f"{file_id}_{role}.wav")

        write_speaker_audio(
            result["diarization"],
            result["audio"],
            result["sr"],
            spk,
            role,
            final_path
        )

        print(f"✅ Сохранено: {final_path}")


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    if os.path.isdir(args.input):
        files = [
            os.path.join(args.input, f)
            for f in os.listdir(args.input)
            if f.lower().endswith(".wav")
        ]

        if not files:
            print("Файлы .wav не найдены")
            return

        for f in files:
            process_file(f, args.output)

    elif os.path.isfile(args.input):
        process_file(args.input, args.output)

    else:
        print("Указанный путь не существует")


if __name__ == "__main__":
    main()


# Код для запуска обработки одного трека
# python ./services/diarization/main.py --input /home/user/wav-parser/audio/filt_audio/file.wav \
# --output /home/user/wav-parser/audio/result

# Код для запуска обработки папки
# python ./services/diarization/main.py --input /home/user/wav-parser/audio/filt_audio/ \
# --output /home/user/wav-parser/audio/result