from pathlib import Path
from pydub import AudioSegment
from typing import Dict, List

from models import Subtitle
from srt_parser import parse_srt, load_role_mapping
from audio_utils import concatenate_segments, match_target_amplitude


def split_audio_by_role(
    audio_path: Path,
    srt_path: Path,
    json_path: Path,
    output_dir: Path,
    normalize: bool = False,
    target_db: float = -28
) -> Dict[str, Path]:
    """
    Разрезает аудио по ролям и сохраняет отдельные файлы для каждой роли.
    Возвращает словарь {роль: путь_к_файлу}.
    """
    audio = AudioSegment.from_file(audio_path)
    subs = parse_srt(srt_path)
    role_map = load_role_mapping(json_path)

    # Группируем интервалы по ролям (только те роли, что есть в маппинге)
    roles = set(role_map.values())
    segments_by_role: Dict[str, List[Tuple[int, int]]] = {role: [] for role in roles}

    for sub in subs:
        role = role_map.get(sub.speaker)
        if role in segments_by_role:
            start_ms = int(sub.start_sec * 1000)
            end_ms = int(sub.end_sec * 1000)
            segments_by_role[role].append((start_ms, end_ms))

    base_name = audio_path.stem
    result_files = {}

    for role, intervals in segments_by_role.items():
        if not intervals:
            print(f"Для роли {role} нет сегментов в {audio_path.name}")
            continue

        combined = concatenate_segments(audio, intervals)
        out_file = output_dir / f"{base_name}_{role.lower()}.wav"
        combined.export(out_file, format="wav")
        print(f"Сохранён файл: {out_file}")
        result_files[role] = out_file

        if normalize:
            normalized = match_target_amplitude(combined, target_db)
            norm_file = output_dir / f"{base_name}_{role.lower()}_norm.wav"
            normalized.export(norm_file, format="wav")
            print(f"Нормализованный файл: {norm_file}")
            result_files[f"{role}_norm"] = norm_file

    return result_files