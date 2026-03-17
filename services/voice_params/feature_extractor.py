import numpy as np
import parselmouth


def compute_pitch(sound, pitch_floor=75, pitch_ceiling=300, time_step=0.01):
    pitch = sound.to_pitch(
        time_step=time_step,
        pitch_floor=pitch_floor,
        pitch_ceiling=pitch_ceiling
    )
    f0 = pitch.selected_array["frequency"]
    f0 = f0[f0 > 0]
    return f0, pitch


def compute_formants(sound, pitch_obj):
    times = pitch_obj.xs()
    f0_values = pitch_obj.selected_array["frequency"]
    formant = sound.to_formant_burg(
        time_step=0.01,
        max_number_of_formants=5,
        maximum_formant=5500,
        window_length=0.025,
        pre_emphasis_from=50
    )

    voiced_mask = f0_values > 0
    F1, F2, F3 = [], [], []
    for t, voiced in zip(times, voiced_mask):
        if not voiced:
            continue
        f1 = formant.get_value_at_time(1, t)
        f2 = formant.get_value_at_time(2, t)
        f3 = formant.get_value_at_time(3, t)
        if None in (f1, f2, f3) or np.isnan(f1) or np.isnan(f2) or np.isnan(f3):
            continue
        F1.append(f1)
        F2.append(f2)
        F3.append(f3)

    return np.array(F1), np.array(F2), np.array(F3)


def extract_features(sound):
    features = {}
    f0, pitch_obj = compute_pitch(sound)
    features["f0_mean"] = float(np.mean(f0)) if len(f0) > 0 else 0.0
    features["f0_variance"] = float(np.var(f0)) if len(f0) > 0 else 0.0

    f1, f2, f3 = compute_formants(sound, pitch_obj)
    for i, formant in enumerate([f1, f2, f3], start=1):
        features[f"f{i}_mean"] = float(np.mean(formant)) if len(formant) > 0 else 0.0
        features[f"f{i}_variance"] = float(np.var(formant)) if len(formant) > 0 else 0.0

    return features