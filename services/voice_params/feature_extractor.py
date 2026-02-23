import numpy as np
import parselmouth


def compute_pitch(sound, pitch_floor=75, pitch_ceiling=300, time_step=0.01):
    '''
    Про голос почему такие ограничения. Без них ложное срабатывание на шуме или форманта за место F0.
    75 — ниже почти нет реального голоса
    300 — выше уже часто ошибки
    '''
    pitch = sound.to_pitch(time_step=time_step,
                           pitch_floor=pitch_floor,
                           pitch_ceiling=pitch_ceiling)
    f0 = pitch.selected_array["frequency"]
    f0 = f0[f0 > 0]  # только с голосом
    return f0, pitch


def compute_formants(sound, pitch_obj):
    '''
    ⚠️ Ошибка №3 (методологическая)

    Ты берёшь все фреймы, включая согласные

    В серьёзной фонетике форманты считают:

    только на voiced

    или только на стабильных участках
    '''
    
    times = pitch_obj.xs()
    f0_values = pitch_obj.selected_array["frequency"]

    formant = sound.to_formant_burg(
        time_step=0.01,
        max_number_of_formants=5,
        maximum_formant=5500,
        window_length=0.025,
        pre_emphasis_from=50         # делаю усиление вручную
    )

    # voiced_mask
    voiced_mask = f0_values > 0

    # собираем форманты на voiced фреймах
    F1, F2, F3 = [], [], []

    for t, voiced in zip(times, voiced_mask):
        if not voiced:
            continue
        f1 = formant.get_value_at_time(1, t)
        f2 = formant.get_value_at_time(2, t)
        f3 = formant.get_value_at_time(3, t)

        if f1 is None or f2 is None or f3 is None:
            continue
        if np.isnan(f1) or np.isnan(f2) or np.isnan(f3):
            continue

        F1.append(f1)
        F2.append(f2)
        F3.append(f3)

    return np.array(F1), np.array(F2), np.array(F3)


def extract_features(sound):
    features = {}

    f0, pitch_obj = compute_pitch(sound)

    # F0 статистика
    features["f0_mean"] = float(np.mean(f0)) if len(f0) > 0 else 0.0
    features["f0_variance"] = float(np.var(f0)) if len(f0) > 0 else 0.0

    # Форманты
    f1, f2, f3 = compute_formants(sound, pitch_obj=pitch_obj)

    for i, formant in enumerate([f1, f2, f3], start=1):
        features[f"f{i}_mean"] = float(np.mean(formant)) if len(formant) > 0 else 0.0
        features[f"f{i}_variance"] = float(np.var(formant)) if len(formant) > 0 else 0.0

    return features