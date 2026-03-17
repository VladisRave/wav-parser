from pathlib import Path
from typing import List, Tuple, Dict, Optional

def find_role_files_recursive(root_dir: str) -> Tuple[List[Path], List[Path]]:
    """
    Рекурсивно ищет все файлы, оканчивающиеся на _user.wav и _assistant.wav.
    Возвращает кортеж (список файлов user, список файлов assistant).
    """
    root = Path(root_dir)
    user_files = list(root.rglob("*_user.wav"))
    assistant_files = list(root.rglob("*_assistant.wav"))
    return user_files, assistant_files

def group_by_call_id(root_dir: str) -> Dict[str, Dict[str, Path]]:
    """
    Рекурсивно ищет файлы _user.wav и _assistant.wav и группирует их по call_id.
    Возвращает словарь вида {call_id: {"user": Path, "assistant": Path}}.
    Пропускает записи, где нет пары.
    """
    root = Path(root_dir)
    result = {}
    for wav in root.rglob("*.wav"):
        name = wav.stem
        if name.endswith("_user"):
            call_id = name[:-5]
            if call_id not in result:
                result[call_id] = {}
            result[call_id]["user"] = wav
        elif name.endswith("_assistant"):
            call_id = name[:-10]
            if call_id not in result:
                result[call_id] = {}
            result[call_id]["assistant"] = wav

    # Удаляем неполные пары (опционально)
    incomplete = [cid for cid, paths in result.items() if len(paths) < 2]
    for cid in incomplete:
        del result[cid]
        print(f"Предупреждение: для звонка {cid} отсутствует один из файлов, пропущен")

    return result