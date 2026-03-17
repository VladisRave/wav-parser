import parselmouth
import numpy as np
from feature_extractor import extract_features


class VoiceParamsPipeline:
    def __init__(self, wav_path):
        self.wav_path = wav_path

    def run(self):
        sound = parselmouth.Sound(str(self.wav_path))
        y = sound.values.T.flatten()
        sr = sound.sampling_frequency
        y = np.nan_to_num(y)
        processed_sound = parselmouth.Sound(y, sampling_frequency=sr)
        return extract_features(processed_sound)