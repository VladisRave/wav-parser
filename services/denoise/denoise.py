import numpy as np
import librosa
import soundfile as sf
import scipy.signal as sps


# 1. High-pass фильтр удаление гула ниже 70 Гц
def highpass_filter(y, sr, cutoff=70):
    sos = sps.butter(2, cutoff, btype="highpass", fs=sr, output="sos")
    return sps.sosfiltfilt(sos, y)

# 2. Лёгкое RMS усиление
def mild_rms_boost(y, target_db=-25, max_boost_db=8):
    rms = np.sqrt(np.mean(y**2) + 1e-9)
    rms_db = 20 * np.log10(rms + 1e-9)

    gain_db = target_db - rms_db
    gain_db = np.clip(gain_db, 0, max_boost_db)

    gain = 10 ** (gain_db / 20)
    return y * gain

# 3. Frame-wise gentle boost (усиление тихих участков для распознавания второго участника)
def frame_gain(y, sr, frame_length=0.025, hop_length=0.01, target_db=-28, max_gain_db=6):
    frame_len_samples = int(frame_length * sr)
    hop_len_samples = int(hop_length * sr)
    y_out = np.zeros_like(y)
    window = np.hanning(frame_len_samples)

    for start in range(0, len(y) - frame_len_samples, hop_len_samples):
        frame = y[start:start + frame_len_samples]
        rms = np.sqrt(np.mean(frame**2) + 1e-9)
        rms_db = 20 * np.log10(rms + 1e-9)
        gain_db = target_db - rms_db
        gain_db = np.clip(gain_db, 0, max_gain_db)
        gain = 10 ** (gain_db / 20)
        y_out[start:start + frame_len_samples] += frame * gain * window

    norm = np.zeros_like(y)
    for start in range(0, len(y) - frame_len_samples, hop_len_samples):
        norm[start:start + frame_len_samples] += window
    norm[norm == 0] = 1.0
    return y_out / norm


# ==========================================================
# 3. Soft limiter
# ==========================================================
def soft_limiter(y, threshold=0.98):
    return np.tanh(y / threshold) * threshold


# ==========================================================
# 4. Финальная нормализация
# ==========================================================
def peak_normalize(y):
    peak = np.max(np.abs(y))
    if peak > 0:
        return y * 0.95 / peak
    return y

def process_audio(input_path, target_sr=16000):
    y, sr = librosa.load(input_path, sr=None, mono=True)

    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    y = highpass_filter(y, sr)
    y = mild_rms_boost(y)
    y = frame_gain(y, sr)
    y = soft_limiter(y)
    y = peak_normalize(y)
    y = np.nan_to_num(y)

    return y, sr

def save_audio(y, sr, output_path):
    sf.write(output_path, y, sr)
    print(f"Файл сохранён: {output_path}")