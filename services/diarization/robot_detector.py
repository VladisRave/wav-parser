import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

ROBOT_PHRASES = [
    "Звонок по вашему заказу. Номер скрыт от исполнителя.",
    "Здравствуйте, вы позвонили в Медико-генетический центр Гинатэк. Чем я могу вам помочь?",
    "Здравствуйте, вы позвонили в Медико-генетический центр Гинатэк. Чем я могу вам помочь? Пожалуйста, подтвердите, что вы хотите, чтобы я связал вас с оператором.",
    "К сожалению, сейчас все операторы заняты. Пожалуйста, оставайтесь на линии, и мы обязательно вам ответим. А если не хотите ждать, напишите нам в личные сообщения в социальных сетях или в вашем личном кабинете.",
]

_MODEL = None

def get_embedder():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        )
    return _MODEL

class RobotDetector:
    def __init__(self, threshold=0.8):
        self.threshold = threshold
        self.model = get_embedder()
        self.robot_emb = self.model.encode(ROBOT_PHRASES, normalize_embeddings=True)

    def is_robot(self, text: str):
        text_emb = self.model.encode([text], normalize_embeddings=True)
        sims = cosine_similarity(text_emb, self.robot_emb)[0]
        idx = int(np.argmax(sims))
        return {
            "is_robot": sims[idx] >= self.threshold,
            "score": float(sims[idx]),
            "matched_phrase": ROBOT_PHRASES[idx]
        }
