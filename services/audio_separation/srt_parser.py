import json
import re
from pathlib import Path
from typing import List

from models import Subtitle


def parse_srt(srt_path: Path) -> List[Subtitle]:
    """
    Парсит SRT файл и преобразует его в список объектов Subtitle.

    Args:
        srt_path: путь к SRT файлу

    Output:
        список объектов Subtitle:
        - index
        - start_sec
        - end_sec
        - speaker
        - text

    """
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()

    blocks = re.split(r"\n\s*\n", content)

    subtitles: List[Subtitle] = []

    time_pattern = (
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )

    for block in blocks:
        lines = block.strip().split("\n")

        if len(lines) < 3:
            continue

        index = int(lines[0])
        time_line = lines[1]

        match = re.match(time_pattern, time_line)
        if not match:
            continue

        start_h, start_m, start_s, start_ms = map(
            int, match.group(1, 2, 3, 4)
        )
        end_h, end_m, end_s, end_ms = map(
            int, match.group(5, 6, 7, 8)
        )

        start_sec = (
            start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
        )
        end_sec = (
            end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
        )

        text_lines = lines[2:]
        full_text = " ".join(text_lines).strip()

        speaker_match = re.match(r"(Speaker \d+):", full_text)

        if speaker_match:
            speaker = speaker_match.group(1)
            clean_text = full_text[len(speaker) + 1 :].strip()
        else:
            speaker = "Unknown"
            clean_text = full_text

        subtitles.append(
            Subtitle(
                index=index,
                start_sec=start_sec,
                end_sec=end_sec,
                speaker=speaker,
                text=clean_text,
            )
        )

    return subtitles


def load_role_mapping(json_path: Path) -> dict:
    """
    Загружает маппинг ролей спикеров из JSON файла.

    Args:
        json_path: путь к JSON файлу с ролями

    Output:
        словарь Python dict
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)