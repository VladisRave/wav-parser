from pathlib import Path
from typing import Dict, List, Tuple


def find_role_files_recursive(
    root_dir: str,
    include_user: bool = True,
    include_assistant: bool = True,
) -> Tuple[List[Path], List[Path]]:
    """
    Рекурсивно ищет аудиофайлы по ролям.

    Args:
        root_dir: корневая папка поиска
        include_user: включать ли user файлы
        include_assistant: включать ли assistant файлы

    Returns:
        tuple:
            - список user файлов
            - список assistant файлов
    """
    root = Path(root_dir)

    user_files: List[Path] = []
    assistant_files: List[Path] = []

    if include_user:
        user_files = list(root.rglob("*_user.wav"))

    if include_assistant:
        assistant_files = list(root.rglob("*_assistant.wav"))

    return user_files, assistant_files


def group_by_call_id(root_dir: str) -> Dict[str, Dict[str, Path]]:
    """
    Группирует файлы по call_id.

    Args:
        root_dir: папка с аудио

    Returns:
        dict:
            {
                call_id: {
                    "user": Path,
                    "assistant": Path
                }
            }
    """
    root = Path(root_dir)
    result: Dict[str, Dict[str, Path]] = {}

    for wav in root.rglob("*.wav"):
        name = wav.stem

        if name.endswith("_user"):
            call_id = name[:-5]
            result.setdefault(call_id, {})["user"] = wav

        elif name.endswith("_assistant"):
            call_id = name[:-10]
            result.setdefault(call_id, {})["assistant"] = wav

    for cid in list(result.keys()):
        if len(result[cid]) < 2:
            print(f"Пропущен {cid}: неполная пара")
            del result[cid]

    return result