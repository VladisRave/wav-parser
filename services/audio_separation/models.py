from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Subtitle:
    """Один субтитр с тайм-кодами и текстом."""
    index: int
    start_sec: float
    end_sec: float
    speaker: str
    text: str


# Тип для маппинга ролей: имя спикера -> роль
RoleMapping = Dict[str, str]