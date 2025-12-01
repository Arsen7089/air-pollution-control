import os
import json
from typing import Optional, Any
from PIL import Image
from abc import ABC, abstractmethod

class AbstractFileStorage(ABC):
    @abstractmethod
    def save_dict(self, data: dict, file_id: str) -> bool:
        """Save a dictionary to a file."""
        pass

    @abstractmethod
    def load_dict(self, file_id: str) -> Optional[dict]:
        """Load a dictionary from a file."""
        pass

    @abstractmethod
    def save_img(self, img: Image.Image, file_id: str) -> bool:
        """Save an image to a file."""
        pass

    @abstractmethod
    def load_img(self, file_id: str) -> Optional[Image.Image]:
        """Load an image from a file."""
        pass


class LocalFileStorage(AbstractFileStorage):
    def __init__(self, storage_dir="storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _full_path(self, file_id: str, ext: str) -> str:
        dir_path = os.path.join(self.storage_dir, os.path.dirname(file_id))
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{os.path.basename(file_id)}.{ext}")

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

    def save_img(self, img: Image.Image, file_id: str) -> bool:
        try:
            path = self._full_path(file_id, "jpg")
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(path, format="JPEG", quality=90)
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    def load_img(self, file_id: str) -> Optional[Image.Image]:
        try:
            path = self._full_path(file_id, "jpg")
            if not os.path.exists(path):
                return None
            img = Image.open(path)
            return img
        except Exception as e:
            print(f"Error loading image: {e}")
            return None

