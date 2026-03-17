from pydub import AudioSegment
from typing import List, Tuple


def match_target_amplitude(sound: AudioSegment, target_dBFS: float) -> AudioSegment:
    """Приводит RMS звука к целевому уровню в dBFS."""
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


def concatenate_segments(audio: AudioSegment, intervals_ms: List[Tuple[int, int]]) -> AudioSegment:
    """
    Вырезает из аудио интервалы в миллисекундах и склеивает их в один непрерывный фрагмент.
    """
    combined = AudioSegment.empty()
    for start_ms, end_ms in intervals_ms:
        segment = audio[start_ms:end_ms]
        combined += segment
    return combined