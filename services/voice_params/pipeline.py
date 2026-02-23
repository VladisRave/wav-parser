import parselmouth
from feature_extractor import extract_features
from processing_audio import frame_normalize
import os
import numpy as np


class VoiceParamsPipeline:
    def __init__(self, wav_path):
        self.wav_path = wav_path
        self.file_id = os.path.splitext(os.path.basename(wav_path))[0]

    def run(self):

        # Загружаем звук
        sound = parselmouth.Sound(self.wav_path)
        y = sound.values.T.flatten()
        sr = sound.sampling_frequency

        # Предобработка
        y = frame_normalize(
            y,
            sr,
            frame_length=0.025,
            hop_length=0.01,
            target_db=-28,
            max_gain_db=12
        )

        y = np.nan_to_num(y)

        # Пересоздаем Sound после обработки
        processed_sound = parselmouth.Sound(y, sampling_frequency=sr)

        # Извлекаем признаки
        features = extract_features(processed_sound)

        return features