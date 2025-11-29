import os
import json
import pickle
import numpy as np
from typing import Optional, Any

class LocalFileStorage:
    def __init__(self, storage_dir="storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _full_path(self, file_id: str, ext: str) -> str:
        dir_path = os.path.join(self.storage_dir, os.path.dirname(file_id))
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{os.path.basename(file_id)}.{ext}")

    # ---- Словники ----
    def save_dict(self, data: dict, file_id: str) -> bool:
        try:
            path = self._full_path(file_id, "txt")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving dict: {e}")
            return False

    def load_dict(self, file_id: str) -> Optional[dict]:
        try:
            path = self._full_path(file_id, "txt")
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading dict: {e}")
            return None

    # ---- NumPy масиви ----
    def save_numpy(self, data: np.ndarray, file_id: str) -> bool:
        try:
            path = self._full_path(file_id, "npy")
            np.save(path, data)
            return True
        except Exception as e:
            print(f"Error saving numpy array: {e}")
            return False

    def load_numpy(self, file_id: str) -> Optional[np.ndarray]:
        try:
            path = self._full_path(file_id, "npy")
            if not os.path.exists(path):
                return None
            return np.load(path, allow_pickle=True)
        except Exception as e:
            print(f"Error loading numpy array: {e}")
            return None

    # ---- Бінарні файли ----
    def save_binary(self, data: Any, file_id: str) -> bool:
        try:
            path = self._full_path(file_id, "pkl")
            with open(path, "wb") as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving binary: {e}")
            return False

    def load_binary(self, file_id: str) -> Optional[Any]:
        try:
            path = self._full_path(file_id, "pkl")
            if not os.path.exists(path):
                return None
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading binary: {e}")
            return None
