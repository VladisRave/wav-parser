import argparse
import logging
import os
import sys
import warnings
from pathlib import Path

os.environ["NEMO_LOG_LEVEL"] = "ERROR"
os.environ["NEMO_LOGGER_LEVEL"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ONELOGGER_ENABLED"] = "0"
os.environ["HYDRA_FULL_ERROR"] = "0"

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)


class SuppressAll:
    """
    Контекстный менеджер для полного подавления вывода stdout и stderr.

    Result:
        Перенаправляет stdout и stderr в os.devnull на время выполнения блока
        кода внутри контекста.
    """

    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._stdout
        sys.stderr = self._stderr


with SuppressAll():
    import torch
    from tqdm import tqdm
    from model import DiarizationEngine
    from utils import find_audio_files


def check_cuda() -> None:
    """
    Проверяет доступность CUDA и выводит информацию о системе и GPU.

    Result:
        Печатает:
        - версию torch
        - доступность CUDA
        - количество GPU
        - текущий GPU
        - имя GPU
        - тестовое устройство tensor
    """
    print("\n===== CUDA DEBUG =====")
    print(f"torch version: {torch.__version__}")
    print(f"cuda available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"gpu count: {torch.cuda.device_count()}")
        print(f"current device: {torch.cuda.current_device()}")
        print(f"device name: {torch.cuda.get_device_name(0)}")

        x = torch.rand(3, 3).cuda()
        print(f"tensor device: {x.device}")
    else:
        print("CUDA NOT AVAILABLE")

    print("======================\n")


def process_path(input_path: str, output_path: str) -> None:
    """
    Обрабатывает все аудиофайлы в директории или файле с помощью диаризации.

    Args:
        input_path: путь к входному файлу или папке с аудио
        output_path: путь для сохранения результатов

    Result:
        - Находит все аудиофайлы в input_path
        - Загружает модели диаризации
        - Обрабатывает каждый файл с прогресс-баром tqdm
        - Сохраняет результаты в output_path
        - Выводит ошибки обработки отдельных файлов
    """
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


def main() -> None:
    """
    Точка входа в программу диаризации.
    """
    check_cuda()

    parser = argparse.ArgumentParser("Diarization Runner")
    parser.add_argument("--input", required=True, help="Input file or folder")
    parser.add_argument("--output", required=True, help="Output folder")

    args = parser.parse_args()
    process_path(args.input, args.output)


if __name__ == "__main__":
    main()


# ==============================
# Примеры запуска
# ==============================

# Для одного файла
# python services/diarization/main.py \
# --input /path/to/file.mp3 \
# --output /path/to/output_folder


# Для всей папки
# python services/diarization/main.py \
# --input /path/to/input_folder \
# --output /path/to/output_folder