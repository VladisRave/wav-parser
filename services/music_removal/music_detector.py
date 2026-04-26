import librosa
import numpy as np
from typing import List, Tuple

from model_loader import load_model


def get_music_intervals(
    audio_path: str,
    sample_rate: int = 16000,
    music_threshold: float = 0.65,
    merge_gap_sec: float = 0.8,
    min_dur_sec: float = 0.5,
    debug: bool = False,
) -> List[Tuple[float, float]]:
    """
    Определяет музыкальные интервалы в аудиофайле с помощью YAMNet.

    Args:
        audio_path: путь к аудиофайлу
        sample_rate: частота дискретизации
        music_threshold: порог вероятности класса Music
        merge_gap_sec: объединение близких интервалов
        min_dur_sec: минимальная длительность интервала
        debug: вывод отладочной информации

    Returns:
        Список интервалов (start_sec, end_sec)
    """

    model, class_names = load_model()
    waveform, _ = librosa.load(audio_path, sr=sample_rate, mono=True)
    music_idx = class_names.index("Music")
    scores, _, _ = model(waveform)
    hop_duration = 0.48  # шаг модели YAMNet

    labels = [
        "music" if score[music_idx] > music_threshold else "other"
        for score in scores
    ]

    intervals: List[Tuple[float, float]] = []

    i = 0
    while i < len(labels):
        if labels[i] == "music":
            start_time = i * hop_duration
            j = i

            while j < len(labels) and labels[j] == "music":
                j += 1

            end_time = j * hop_duration
            intervals.append((start_time, end_time))

            i = j
        else:
            i += 1

    if not intervals:
        return []

    merged: List[Tuple[float, float]] = []

    cur_start, cur_end = intervals[0]

    for start, end in intervals[1:]:
        if start - cur_end <= merge_gap_sec:
            cur_end = max(cur_end, end)
        else:
            if cur_end - cur_start >= min_dur_sec:
                merged.append((cur_start, cur_end))

            cur_start, cur_end = start, end

    if cur_end - cur_start >= min_dur_sec:
        merged.append((cur_start, cur_end))


    return merged