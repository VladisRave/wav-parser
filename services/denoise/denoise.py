import numpy as np
import librosa
import soundfile as sf
import scipy.signal as sps


# ===============================
# Фильтры и усиление
# ===============================

def highpass_filter(y, sr, cutoff=70, order=4):
    """Удаляем низкочастотный гул (можно менять cutoff)."""
    sos = sps.butter(order, cutoff, btype="highpass", fs=sr, output="sos")
    return sps.sosfiltfilt(sos, y)


def adaptive_frame_gain(y, sr, frame_length=0.025, hop_length=0.01, target_db=-28, max_gain_db=6):
    """
    Усиление тихих фреймов без клиппинга.
    Меньшее значение max_gain_db даёт менее агрессивное усиление.
    """
    frame_len = int(frame_length * sr)
    hop_len = int(hop_length * sr)
    y_out = np.zeros_like(y)
    norm = np.zeros_like(y)
    window = np.hanning(frame_len)

    for start in range(0, len(y) - frame_len + 1, hop_len):
        frame = y[start:start + frame_len]
        rms = np.sqrt(np.mean(frame**2) + 1e-12)
        rms_db = 20 * np.log10(rms + 1e-12)
        gain_db = np.clip(target_db - rms_db, 0, max_gain_db)
        gain = 10 ** (gain_db / 20)
        y_out[start:start + frame_len] += frame * gain * window
        norm[start:start + frame_len] += window

    norm[norm == 0] = 1.0
    y_out /= norm
    return np.nan_to_num(y_out)


def soft_limiter(y, threshold=0.98):
    """Мягкий лимитер для предотвращения клиппинга. Можно отключить, убрав вызов."""
    return np.tanh(y / threshold) * threshold


def peak_normalize(y, peak_level=0.95):
    """Подгоняем сигнал под максимум без клиппинга. Можно отключить."""
    peak = np.max(np.abs(y))
    if peak > 0:
        y = y * (peak_level / peak)
    return np.nan_to_num(y)


def process_audio(input_path, target_sr=16000, target_db=-28, max_gain_db=6, hpf_cutoff=70):
    """
    Загружает аудио, применяет HPF, адаптивное усиление, лимитер и пиковую нормализацию.
    Для менее грубой обработки:
        - увеличить hpf_cutoff (чтобы меньше резать низы) или использовать меньший порядок фильтра
        - уменьшить max_gain_db (например, до 3)
        - увеличить target_db (например, -20 вместо -28)
        - отказаться от лимитера или пиковой нормализации (закомментировать соответствующие строки)
    """
    y, sr = librosa.load(input_path, sr=None, mono=True)

    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    # High-pass фильтр (убираем инфранизкие частоты)
    y = highpass_filter(y, sr, cutoff=hpf_cutoff)

    # Frame-wise RMS нормализация (выравнивание громкости)
    y = adaptive_frame_gain(y, sr, target_db=target_db, max_gain_db=max_gain_db)

    # Опциональные этапы: можно отключить, закомментировав
    y = soft_limiter(y)          # можно убрать, если не нужен
    y = peak_normalize(y)         # можно убрать

    return y, sr


def save_audio(y, sr, output_path):
    sf.write(output_path, y, sr)
    print(f"Файл сохранён: {output_path}")