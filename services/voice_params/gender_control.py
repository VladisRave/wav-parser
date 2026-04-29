import sys
import torch
from pathlib import Path

# Определяем путь к модели
current_dir = Path(__file__).parent                                 
project_root = current_dir.parent.parent                            
model_path = project_root / "external" / "voice-gender-classifier"

# Добавляем в sys.path
sys.path.insert(0, str(model_path))

# Проверяем, что model.py действительно существует (для отладки)
if not (model_path / "model.py").exists():
    raise FileNotFoundError(f"model.py not found in {model_path}")

from model import ECAPA_gender

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = ECAPA_gender.from_pretrained("JaesungHuh/voice-gender-classifier")
_model.eval()
_model.to(_device)


def get_gender(audio_path: str) -> str:
    """
    Определяет пол по аудиофайлу.

    Args:
        audio_path: путь к .wav файлу

    Returns:
        str: "male", "female" или "unknown"
    """
    with torch.no_grad():
        prediction = _model.predict(audio_path, device=_device)
        return prediction