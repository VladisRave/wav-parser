from pydub import AudioSegment
from typing import List, Tuple


def concatenate_segments(audio: AudioSegment, intervals_ms: List[Tuple[int, int]]) -> AudioSegment:
    """
    Вырезает из аудио интервалы в миллисекундах и склеивает их в один непрерывный фрагмент.
    """
    combined = AudioSegment.empty()
    for start_ms, end_ms in intervals_ms:
        segment = audio[start_ms:end_ms]
        combined += segment
    return combined