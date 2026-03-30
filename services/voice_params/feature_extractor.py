import numpy as np
import parselmouth


def compute_pitch(sound, pitch_floor=75, pitch_ceiling=300, time_step=0.01):
    """Возвращает массив F0 и объект Pitch для дальнейших вычислений"""
    pitch = sound.to_pitch(time_step=time_step, pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    f0 = pitch.selected_array["frequency"]
    f0 = f0[f0 > 0]
    return f0, pitch

def compute_jitter_shimmer(sound):
    """Jitter/Шум и дрожание амплитуды"""
    point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 300)
    jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    shimmer = parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    return float(jitter), float(shimmer)

def compute_intensity(sound):
    """Средняя и стандартное отклонение громкости"""
    intensity = sound.to_intensity()
    values = intensity.values[intensity.values != 0]
    mean_intensity = float(np.mean(values)) if len(values) > 0 else 0.0
    std_intensity = float(np.std(values)) if len(values) > 0 else 0.0
    return mean_intensity, std_intensity

def compute_formants(sound, pitch_obj, max_formant=5500):
    """F1–F3"""
    times = pitch_obj.xs()
    f0_values = pitch_obj.selected_array["frequency"]
    formant = sound.to_formant_burg(time_step=0.01, max_number_of_formants=5,
                                    maximum_formant=max_formant, window_length=0.025,
                                    pre_emphasis_from=50)
    voiced_mask = f0_values > 0
    F_list = [[] for _ in range(3)]  # F1–F3
    for t, voiced in zip(times, voiced_mask):
        if not voiced:
            continue
        for i in range(3):
            val = formant.get_value_at_time(i+1, t)
            if val is None or np.isnan(val):
                continue
            F_list[i].append(val)
    return [np.array(f) for f in F_list]

def compute_slope(array):
    """Наклон времени для F0 или форманты"""
    if len(array) < 2:
        return 0.0
    x = np.arange(len(array))
    slope = np.polyfit(x, array, 1)[0]
    return float(slope)

def compute_speech_rate(sound):
    """Оценка скорости речи: число слогоподобных событий / продолжительность"""
    duration = sound.get_total_duration()
    pitch = sound.to_pitch()
    f0 = pitch.selected_array["frequency"]
    voiced = f0 > 0
    syllable_estimate = np.sum(np.diff(voiced.astype(int)) == 1)
    return float(syllable_estimate / duration) if duration > 0 else 0.0

def extract_features(sound):
    features = {}

    # F0
    f0, pitch_obj = compute_pitch(sound)
    features["f0_mean"] = float(np.mean(f0)) if len(f0) > 0 else 0.0
    features["f0_variance"] = float(np.var(f0)) if len(f0) > 0 else 0.0
    features["f0_slope"] = compute_slope(f0)

    # Форманты F1–F3
    F1, F2, F3 = compute_formants(sound, pitch_obj)
    formants = [F1, F2, F3]
    for i, formant in enumerate(formants, start=1):
        features[f"f{i}_mean"] = float(np.mean(formant)) if len(formant) > 0 else 0.0
        features[f"f{i}_variance"] = float(np.var(formant)) if len(formant) > 0 else 0.0
        features[f"f{i}_slope"] = compute_slope(formant)
        features[f"f{i}_range"] = (np.max(formant) - np.min(formant)) if len(formant) > 0 else 0.0

    # Jitter / Shimmer
    jitter, shimmer = compute_jitter_shimmer(sound)
    features["jitter"] = jitter
    features["shimmer"] = shimmer

    # Intensity
    mean_intensity, std_intensity = compute_intensity(sound)
    features["intensity_mean"] = mean_intensity
    features["intensity_std"] = std_intensity

    # Speech rate
    features["speech_rate"] = compute_speech_rate(sound)

    return features