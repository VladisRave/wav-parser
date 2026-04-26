import librosa
import numpy as np
import soundfile as sf
import scipy.signal as sps
from typing import Tuple


EPS = 1e-12


def highpass_filter(
    y: np.ndarray,
    sr: int,
    cutoff: float = 70,
    order: int = 4,
) -> np.ndarray:
    """
    High-pass фильтр для удаления низкочастотного гула.

    Args:
        y: аудиосигнал
        sr: частота дискретизации
        cutoff: частота среза
        order: порядок фильтра

    Returns:
        Отфильтрованный сигнал
    """
    sos = sps.butter(
        order,
        cutoff,
        btype="highpass",
        fs=sr,
        output="sos",
    )

    return sps.sosfiltfilt(sos, y)


def adaptive_frame_gain(
    y: np.ndarray,
    sr: int,
    frame_length: float = 0.025,
    hop_length: float = 0.01,
    target_db: float = -28,
    max_gain_db: float = 6,
) -> np.ndarray:
    """
    Усиление тихих участков аудио без клиппинга.

    Args:
        y: аудиосигнал
        sr: частота дискретизации
        frame_length: длина фрейма (сек)
        hop_length: шаг фрейма (сек)
        target_db: целевая громкость
        max_gain_db: максимальное усиление

    Returns:
        Обработанный сигнал
    """

    frame_len = int(frame_length * sr)
    hop_len = int(hop_length * sr)

    y_out = np.zeros_like(y)
    norm = np.zeros_like(y)

    window = np.hanning(frame_len)

    for start in range(0, len(y) - frame_len + 1, hop_len):
        frame = y[start:start + frame_len]

        rms = np.sqrt(np.mean(frame ** 2) + EPS)
        rms_db = 20 * np.log10(rms + EPS)

        gain_db = np.clip(target_db - rms_db, 0, max_gain_db)
        gain = 10 ** (gain_db / 20)

        y_out[start:start + frame_len] += frame * gain * window
        norm[start:start + frame_len] += window

    norm[norm == 0] = 1.0

    y_out /= norm

    return np.nan_to_num(y_out)


def soft_limiter(
    y: np.ndarray,
    threshold: float = 0.98,
) -> np.ndarray:
    """
    Мягкий лимитер для предотвращения клиппинга.

    Args:
        y: аудиосигнал
        threshold: порог лимитера

    Returns:
        Ограниченный сигнал
    """
    return np.tanh(y / threshold) * threshold


def peak_normalize(
    y: np.ndarray,
    peak_level: float = 0.95,
) -> np.ndarray:
    """
    Пиковая нормализация сигнала.

    Args:
        y: аудиосигнал
        peak_level: максимальный уровень

    Returns:
        Нормализованный сигнал
    """
    peak = np.max(np.abs(y))

    if peak > 0:
        y = y * (peak_level / peak)

    return np.nan_to_num(y)


def process_audio(
    input_path: str,
    target_sr: int = 16000,
    target_db: float = -28,
    max_gain_db: float = 6,
    hpf_cutoff: float = 70,
) -> Tuple[np.ndarray, int]:
    """
    Основная функция обработки аудио.

    Этапы обработки:
    1. Загрузка аудио
    2. Ресемплинг
    3. High-pass фильтр
    4. Выравнивание громкости
    5. Лимитер
    6. Пиковая нормализация

    Args:
        input_path: путь к аудиофайлу
        target_sr: целевая частота дискретизации
        target_db: целевая громкость
        max_gain_db: максимальное усиление
        hpf_cutoff: частота high-pass фильтра

    Returns:
        Обработанный сигнал и частота дискретизации
    """

    y, sr = librosa.load(
        input_path,
        sr=None,
        mono=True,
    )

    if sr != target_sr:
        y = librosa.resample(
            y,
            orig_sr=sr,
            target_sr=target_sr,
        )
        sr = target_sr

    # High-pass фильтр
    y = highpass_filter(
        y,
        sr,
        cutoff=hpf_cutoff,
    )

    # Выравнивание громкости
    y = adaptive_frame_gain(
        y,
        sr,
        target_db=target_db,
        max_gain_db=max_gain_db,
    )

    # Лимитер
    y = soft_limiter(y)

    # Пиковая нормализация
    y = peak_normalize(y)

    return y, sr


def save_audio(
    y: np.ndarray,
    sr: int,
    output_path: str,
) -> None:
    """
    Сохранение аудиофайла.

    Args:
        y: аудиосигнал
        sr: частота дискретизации
        output_path: путь сохранения
    """

    sf.write(output_path, y, sr)

    print(f"Файл сохранён: {output_path}")