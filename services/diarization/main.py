import argparse
import torch
from pathlib import Path
from tqdm import tqdm
from model import DiarizationEngine
from utils import find_audio_files


def check_cuda():
    print("\n===== CUDA DEBUG =====")
    print("torch version:", torch.__version__)
    print("cuda available:", torch.cuda.is_available())

    if torch.cuda.is_available():
        print("gpu count:", torch.cuda.device_count())
        print("current device:", torch.cuda.current_device())
        print("device name:", torch.cuda.get_device_name(0))
        x = torch.rand(3, 3).cuda()
        print("tensor device:", x.device)
    else:
        print("CUDA NOT AVAILABLE")

    print("======================\n")


def process_path(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    audio_files = find_audio_files(input_path)
    if not audio_files:
        print(f"No audio files found in {input_path}")
        return

    print(f"Found {len(audio_files)} files to diarize")

    engine = DiarizationEngine()
    engine.load_models()

    for audio_file in tqdm(audio_files, desc="Diarization"):
        try:
            engine.process_file(audio_file, output_path)
        except Exception as e:
            print(f"\nError processing {audio_file.name}: {e}")
            continue

    engine.unload()


if __name__ == "__main__":
    check_cuda()

    parser = argparse.ArgumentParser("Diarization Runner")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    process_path(args.input, args.output)

# Код для запуска обработки одного трека
# python ./services/diarization/main.py --input /home/user/wav-parser/audio/filt_audio/file.wav \
# --output /home/user/wav-parser/audio/result

# Код для запуска обработки папки
# python ./services/diarization/main.py --input /home/user/wav-parser/audio/tracks/ \
# --output /home/user/wav-parser/audio/tracks