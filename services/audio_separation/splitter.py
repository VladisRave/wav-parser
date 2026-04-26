from pathlib import Path
from typing import Dict, List, Tuple

from pydub import AudioSegment

from audio_utils import concatenate_segments
from srt_parser import load_role_mapping, parse_srt


def split_audio_by_role(
    audio_path: Path,
    srt_path: Path,
    json_path: Path,
    output_dir: Path,
    selected_roles: set[str] | None = None,
) -> Dict[str, Path]:
    """
    Разделяет аудиофайл на дорожки по ролям спикеров.

    Args:
        audio_path: путь к аудиофайлу
        srt_path: путь к SRT файлу
        json_path: путь к JSON с маппингом Speaker → Role
        output_dir: директория для сохранения результата
        selected_roles: набор ролей для обработки (если None — все роли)

    Input:
        - аудио файл
        - SRT с таймингами и спикерами
        - JSON с ролями
        - фильтр ролей (опционально)

    Output:
        dict:
        {
            "USER": Path,
            "ASSISTANT": Path,
            "ROBOT": Path
        }

    Result:
        - читает аудио
        - парсит SRT
        - применяет role mapping
        - фильтрует роли по selected_roles
        - склеивает сегменты
        - сохраняет отдельные аудиофайлы
    """
    audio = AudioSegment.from_file(audio_path)

    subs = parse_srt(srt_path)
    role_map = load_role_mapping(json_path)


    if not role_map:
        print(f"Предупреждение: role_map пустой для {audio_path}, пропускаем")
        return {}

    roles = set(role_map.values())

    if selected_roles:
        roles = roles.intersection(selected_roles)

    segments_by_role: Dict[str, List[Tuple[int, int]]] = {
        role: [] for role in roles
    }

    for sub in subs:
        role = role_map.get(sub.speaker)

        if role not in segments_by_role:
            continue

        start_ms = int(sub.start_sec * 1000)
        end_ms = int(sub.end_sec * 1000)

        segments_by_role[role].append((start_ms, end_ms))

    base_name = audio_path.stem
    result_files: Dict[str, Path] = {}

    output_dir.mkdir(parents=True, exist_ok=True)

    for role, intervals in segments_by_role.items():
        if not intervals:
            print(f"Нет сегментов для роли {role} в {audio_path.name}")
            continue

        intervals.sort(key=lambda x: x[0])

        combined_audio = concatenate_segments(audio, intervals)

        out_file = output_dir / f"{base_name}_{role.lower()}.wav"

        combined_audio.export(out_file, format="wav")

        print(f"Сохранён файл: {out_file}")

        result_files[role] = out_file

    return result_files