from pathlib import Path
from typing import List

AUDIO_EXTENSIONS = [".wav"]


def find_audio_files(input_path: Path) -> List[Path]:
    """
    Ищет аудиофайлы для обработки в подпапках входной директории.

    Args:
        input_path: путь к директории с аудиофайлами

    Returns:
        список путей к аудиофайлам (.wav)

    Result:
        - Проверяет, что input_path является директорией
        - Проходит по всем подпапкам (исключая "input")
        - Находит .wav файлы
        - Исключает файлы, для которых уже существует .srt (уже обработаны)
        - Возвращает список файлов для диаризации
    """
    audio_files: List[Path] = []

    if not input_path.is_dir():
        return audio_files

    for subdir in sorted(input_path.iterdir()):
        if not subdir.is_dir():
            continue

        if subdir.name == "input":
            continue

        for wav in subdir.glob("*.wav"):
            srt = wav.with_suffix(".srt")

            if srt.exists():
                continue

            audio_files.append(wav)

    return audio_files