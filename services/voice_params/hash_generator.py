import hashlib
import json
import os

HASH_LENGTH = 9


class FileHasher:
    def __init__(self, json_path=None):
        self.mapping = {}
        self.json_path = json_path

    def hash_name(self, original_name):
        h = hashlib.md5(original_name.encode("utf-8")).hexdigest()
        short_hash = h[:HASH_LENGTH]
        self.mapping[short_hash] = original_name
        return short_hash

    def save_json(self, path=None):
        save_path = path or self.json_path
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.mapping, f, indent=4, ensure_ascii=False)
            print(f"Mapping saved to: {save_path}")

    def get_original_name(self, hash_name):
        return self.mapping.get(hash_name)