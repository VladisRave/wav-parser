import os
import librosa
import numpy as np
import tempfile
import soundfile as sf
from diarize import load_diarization_pipeline
from asr import load_asr
from robot_detector import RobotDetector
from speaker_selector import select_human_speakers


class DiarizationPipeline:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.filename = os.path.basename(audio_path)
        self.diar_pipeline, self.min_spk, self.max_spk = load_diarization_pipeline(audio_path)
        self.asr = load_asr()
        self.robot_detector = RobotDetector()
        self.y, self.sr = librosa.load(audio_path, sr=None, mono=True)

    def run(self):
        diarization = self.diar_pipeline(
            self.audio_path,
            min_speakers=self.min_spk,
            max_speakers=self.max_spk
        )

        speakers_info = []

        for speaker in diarization.labels():

            segments = [
                (seg.start, seg.end)
                for seg, _, spk in diarization.itertracks(yield_label=True)
                if spk == speaker
            ][:3]

            if not segments:
                continue

            text = self._transcribe_segments(segments)

            if not text.strip():
                robot = {"is_robot": True}
            else:
                robot = self.robot_detector.is_robot(text)

            speakers_info.append({
                "speaker": speaker,
                "segments": segments,
                "robot": robot
            })



        # два случая один человек или двое
        if "clean_filt" in self.filename:
            selected_speakers = select_human_speakers(speakers_info, limit=2)
        else:
            selected_speakers = select_human_speakers(speakers_info, limit=1)

        return {
            "speakers": selected_speakers,
            "diarization": diarization,
            "audio": self.y,
            "sr": self.sr
        }

    def _transcribe_segments(self, segments):

        if not segments:
            return ""

        merged = np.concatenate([
            self.y[int(s*self.sr):int(e*self.sr)]
            for s, e in segments
        ])

        if merged.size == 0:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, merged, self.sr)
            text = self.asr.transcribe_longform(tmp.name)
            os.remove(tmp.name)

        if isinstance(text, list):
            text = " ".join(t.get("transcription", "") for t in text)

        return text
