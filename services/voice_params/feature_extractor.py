import numpy as np
import parselmouth


def ensure_min_duration(sound, min_duration: float = 3.0):
    """
    Дополняет аудио тишиной, если длительность меньше min_duration.

    Args:
        sound: parselmouth.Sound
        min_duration: минимальная длительность в секундах

    Returns:
        parselmouth.Sound: аудио с минимальной длительностью
    """
    duration = sound.get_total_duration()

    if duration >= min_duration:
        return sound

    sr = sound.sampling_frequency
    signal = sound.values

    target_samples = int(min_duration * sr)
    current_samples = signal.shape[1]
    pad_length = target_samples - current_samples

    padded_signal = np.pad(
        signal,
        ((0, 0), (0, pad_length)),
        mode="constant",
    )

    return parselmouth.Sound(padded_signal, sampling_frequency=sr)


def cut_max_duration(sound, max_duration: float = 300.0):
    """
    Обрезает аудио до максимальной длительности.

    Args:
        sound: parselmouth.Sound
        max_duration: максимальная длительность в секундах

    Returns:
        parselmouth.Sound
    """
    duration = sound.get_total_duration()

    if duration <= max_duration:
        return sound

    return sound.extract_part(
        from_time=0,
        to_time=max_duration,
        preserve_times=False,
    )


def compute_pitch(
    sound,
    pitch_floor: int = 75,
    pitch_ceiling: int = 300,
    time_step: float = 0.01,
):
    """
    Вычисляет основной тон (F0).

    Args:
        sound: parselmouth.Sound
        pitch_floor: нижняя граница pitch
        pitch_ceiling: верхняя граница pitch
        time_step: шаг анализа

    Returns:
        tuple[np.ndarray, parselmouth.Pitch]
    """
    pitch = sound.to_pitch(
        time_step=time_step,
        pitch_floor=pitch_floor,
        pitch_ceiling=pitch_ceiling,
    )

    f0 = pitch.selected_array["frequency"]
    f0 = f0[f0 > 0]

    return f0, pitch


def compute_jitter_shimmer(sound):
    """
    Вычисляет jitter и shimmer.

    Args:
        sound: parselmouth.Sound

    Returns:
        tuple[float, float]
    """
    point_process = parselmouth.praat.call(
        sound,
        "To PointProcess (periodic, cc)",
        75,
        300,
    )

    jitter = parselmouth.praat.call(
        point_process,
        "Get jitter (local)",
        0, 0, 0.0001, 0.02, 1.3,
    )

    shimmer = parselmouth.praat.call(
        [sound, point_process],
        "Get shimmer (local)",
        0, 0, 0.0001, 0.02, 1.3, 1.6,
    )

    return float(jitter), float(shimmer)


def compute_intensity(sound):
    """
    Вычисляет среднюю и стандартную интенсивность.

    Args:
        sound: parselmouth.Sound

    Returns:
        tuple[float, float]
    """
    intensity = sound.to_intensity()
    values = intensity.values[intensity.values != 0]

    mean_intensity = float(np.mean(values)) if len(values) > 0 else 0.0
    std_intensity = float(np.std(values)) if len(values) > 0 else 0.0

    return mean_intensity, std_intensity


def compute_formants(sound, pitch_obj, max_formant: int = 5500):
    """
    Извлекает форманты F1–F4.

    Args:
        sound: parselmouth.Sound
        pitch_obj: объект pitch
        max_formant: максимальная частота формант

    Returns:
        list[np.ndarray]
    """
    times = pitch_obj.xs()
    f0_values = pitch_obj.selected_array["frequency"]

    formant = sound.to_formant_burg(
        time_step=0.01,
        max_number_of_formants=5,
        maximum_formant=max_formant,
        window_length=0.025,
        pre_emphasis_from=50,
    )

    voiced_mask = f0_values > 0
    f_list = [[] for _ in range(4)]

    for t, voiced in zip(times, voiced_mask):
        if not voiced:
            continue

        for i in range(4):
            val = formant.get_value_at_time(i + 1, t)

            if val is None or np.isnan(val):
                continue

            f_list[i].append(val)

    return [np.array(f) for f in f_list]


def compute_speech_rate(sound):
    """
    Оценка скорости речи.

    Args:
        sound: parselmouth.Sound

    Returns:
        float
    """
    duration = sound.get_total_duration()

    pitch = sound.to_pitch()
    f0 = pitch.selected_array["frequency"]

    voiced = f0 > 0
    syllable_estimate = np.sum(np.diff(voiced.astype(int)) == 1)

    return float(syllable_estimate / duration) if duration > 0 else 0.0


def compute_statistics(array):
    """
    Статистики массива значений.

    Args:
        array: np.ndarray

    Returns:
        dict
    """
    if len(array) == 0:
        return {
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "range": 0.0,
        }

    return {
        "median": float(np.median(array)),
        "std": float(np.std(array)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "range": float(np.max(array) - np.min(array)),
    }


def extract_features(sound):
    """
    Извлекает полный набор акустических признаков.

    Args:
        sound: parselmouth.Sound

    Returns:
        dict
    """
    original_duration = sound.get_total_duration()

    sound = cut_max_duration(sound)
    sound = ensure_min_duration(sound)

    features = {"total_duration": original_duration}

    f0, pitch_obj = compute_pitch(sound)
    f0_stats = compute_statistics(f0)

    for key, value in f0_stats.items():
        features[f"f0_{key}"] = value

    f1, f2, f3, f4 = compute_formants(sound, pitch_obj)

    for i, formant in enumerate([f1, f2, f3, f4], start=1):
        stats = compute_statistics(formant)

        for key, value in stats.items():
            features[f"f{i}_{key}"] = value

    jitter, shimmer = compute_jitter_shimmer(sound)
    features["jitter"] = jitter
    features["shimmer"] = shimmer

    mean_intensity, std_intensity = compute_intensity(sound)
    features["intensity_mean"] = mean_intensity
    features["intensity_std"] = std_intensity

    features["speech_rate"] = compute_speech_rate(sound)

    return features