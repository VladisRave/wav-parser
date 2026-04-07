import numpy as np
import parselmouth
from scipy.stats import skew, kurtosis
import librosa



def ensure_min_duration(sound, min_duration=1.0):
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
        mode="constant"
    )

    return parselmouth.Sound(padded_signal, sampling_frequency=sr)

def compute_pitch(sound, pitch_floor=75, pitch_ceiling=300, time_step=0.01):
    pitch = sound.to_pitch(time_step=time_step, pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    f0 = pitch.selected_array["frequency"]
    f0 = f0[f0 > 0]
    return f0, pitch


def compute_jitter_shimmer(sound):
    point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 300)
    jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    shimmer = parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    return float(jitter), float(shimmer)


def compute_intensity(sound):
    intensity = sound.to_intensity()
    values = intensity.values[intensity.values != 0]
    mean_intensity = float(np.mean(values)) if len(values) > 0 else 0.0
    std_intensity = float(np.std(values)) if len(values) > 0 else 0.0
    return mean_intensity, std_intensity


def compute_formants(sound, pitch_obj, max_formant=5500):
    times = pitch_obj.xs()
    f0_values = pitch_obj.selected_array["frequency"]

    formant = sound.to_formant_burg(
        time_step=0.01,
        max_number_of_formants=5,
        maximum_formant=max_formant,
        window_length=0.025,
        pre_emphasis_from=50
    )

    voiced_mask = f0_values > 0
    F_list = [[] for _ in range(4)]

    for t, voiced in zip(times, voiced_mask):
        if not voiced:
            continue

        for i in range(4):
            val = formant.get_value_at_time(i + 1, t)
            if val is None or np.isnan(val):
                continue

            F_list[i].append(val)

    return [np.array(f) for f in F_list]


def compute_speech_rate(sound):
    duration = sound.get_total_duration()
    pitch = sound.to_pitch()
    f0 = pitch.selected_array["frequency"]

    voiced = f0 > 0
    syllable_estimate = np.sum(np.diff(voiced.astype(int)) == 1)

    return float(syllable_estimate / duration) if duration > 0 else 0.0


def compute_statistics(array):

    if len(array) == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "variance": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "range": 0.0,
            "skew": 0.0,
            "kurtosis": 0.0,
            "cv": 0.0
        }

    return {
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "variance": float(np.var(array)),
        "std": float(np.std(array)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "range": float(np.max(array) - np.min(array)),
        "skew": float(skew(array)),
        "kurtosis": float(kurtosis(array)),
        "cv": float(np.std(array) / np.mean(array)) if np.mean(array) != 0 else 0.0
    }

def compute_mfcc(sound, sr=16000, n_mfcc=13):

    signal = sound.values[0]
    
    mfcc = librosa.feature.mfcc(
        y=signal,
        sr=sr,
        n_mfcc=n_mfcc
    )

    features = {}

    for i in range(n_mfcc):
        stats = compute_statistics(mfcc[i])
        
        for key, value in stats.items():
            features[f"mfcc{i+1}_{key}"] = value

    return features

def compute_energy(sound):

    signal = sound.values[0]

    rms = librosa.feature.rms(y=signal)[0]

    return compute_statistics(rms)

def compute_spectral(sound, sr=16000):

    signal = sound.values[0]

    spectral_centroid = librosa.feature.spectral_centroid(
        y=signal, sr=sr)[0]

    spectral_bandwidth = librosa.feature.spectral_bandwidth(
        y=signal, sr=sr)[0]

    spectral_rolloff = librosa.feature.spectral_rolloff(
        y=signal, sr=sr)[0]

    spectral_flatness = librosa.feature.spectral_flatness(
        y=signal)[0]

    features = {}

    spectral_dict = {
        "centroid": spectral_centroid,
        "bandwidth": spectral_bandwidth,
        "rolloff": spectral_rolloff,
        "flatness": spectral_flatness
    }

    for name, values in spectral_dict.items():

        stats = compute_statistics(values)

        for key, value in stats.items():
            features[f"spectral_{name}_{key}"] = value

    return features

def extract_features(sound):

    sound = ensure_min_duration(sound)

    features = {}

    # F0
    f0, pitch_obj = compute_pitch(sound)
    f0_stats = compute_statistics(f0)
    for key, value in f0_stats.items():
        features[f"f0_{key}"] = value

    # Форманты
    F1, F2, F3, F4 = compute_formants(sound, pitch_obj)
    formants = [F1, F2, F3, F4]
    for i, formant in enumerate(formants, start=1):

        stats = compute_statistics(formant)

        for key, value in stats.items():
            features[f"f{i}_{key}"] = value

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
    # MFCC
    mfcc_features = compute_mfcc(sound)
    features.update(mfcc_features)

    # Energy
    energy_stats = compute_energy(sound)
    for key, value in energy_stats.items():
        features[f"energy_{key}"] = value

    # Spectral
    spectral_features = compute_spectral(sound)
    features.update(spectral_features)  

    return features