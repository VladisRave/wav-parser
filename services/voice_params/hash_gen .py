# hash_filenames.py
import hashlib
import json
import os

HASH_LENGTH = 9  # сколько символов хэша использовать

class FileHasher:
    def __init__(self, json_path=None):
        """
        json_path: путь для сохранения JSON с соответствием hash -> original name
        """
        self.mapping = {}
        self.json_path = json_path

    def hash_name(self, original_name):
        """
        Генерирует хэш из оригинального названия файла.
        Возвращает строку из HASH_LENGTH символов.
        """
        # Используем md5, можно заменить на sha256 для более уникальных значений
        h = hashlib.md5(original_name.encode("utf-8")).hexdigest()
        short_hash = h[:HASH_LENGTH]
        self.mapping[short_hash] = original_name
        return short_hash

    def save_json(self, path=None):
        """
        Сохраняет mapping в JSON файл
        """
        save_path = path or self.json_path
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.mapping, f, indent=4, ensure_ascii=False)
            print(f"Mapping saved to: {save_path}")

    def get_original_name(self, hash_name):
        """
        Возвращает исходное имя по хэшу
        """
        return self.mapping.get(hash_name)