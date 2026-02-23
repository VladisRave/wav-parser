import numpy as np


def frame_normalize(y, sr, frame_length=0.025, hop_length=0.01, target_db=-28, max_gain_db=12):
    """
    Нормализация RMS по фреймам для выравнивания громкости между участниками.
    Для тихих участков — повышает амплитуду, громкие не режет сильно.
    Используется оконная обработка Хэннинга и компенсация перекрытий.
    """
    frame_len_samples = int(frame_length * sr)
    hop_len_samples = int(hop_length * sr)
    y_out = np.zeros_like(y)
    window = np.hanning(frame_len_samples)

    for start in range(0, len(y) - frame_len_samples, hop_len_samples):
        frame = y[start:start + frame_len_samples]
        rms = np.sqrt(np.mean(frame**2) + 1e-12)  # избегаем деления на ноль
        rms_db = 20 * np.log10(rms + 1e-12)
        gain_db = target_db - rms_db
        gain_db = np.clip(gain_db, 0, max_gain_db)  # ограничиваем усиление
        gain = 10 ** (gain_db / 20)
        y_out[start:start + frame_len_samples] += frame * gain * window

    # компенсация перекрытий окон
    norm = np.zeros_like(y)
    for start in range(0, len(y) - frame_len_samples, hop_len_samples):
        norm[start:start + frame_len_samples] += window
    norm[norm == 0] = 1.0

    y_final = y_out / norm
    y_final = np.nan_to_num(y_final)  # убираем NaN и inf
    return y_final
