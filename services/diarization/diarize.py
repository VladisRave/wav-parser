import torch
import os
from pyannote.audio import Pipeline

def load_diarization_pipeline(audio_path):
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN not set")

    filename = os.path.basename(audio_path)
    if "clean" in filename:
        model = "pyannote/speaker-diarization-3.1"
        min_spk, max_spk = 2, 5
    else:
        model = "pyannote/speaker-diarization@2.1"
        min_spk, max_spk = 2, 2

    pipeline = Pipeline.from_pretrained(model, use_auth_token=hf_token)
    pipeline.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    return pipeline, min_spk, max_spk
