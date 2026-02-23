import torch
from transformers import AutoModel

_ASR_MODEL = None

def load_asr():
    global _ASR_MODEL
    if _ASR_MODEL is None:
        _ASR_MODEL = AutoModel.from_pretrained(
            "ai-sage/GigaAM-v3",
            revision="e2e_rnnt",
            trust_remote_code=True
        ).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    return _ASR_MODEL
