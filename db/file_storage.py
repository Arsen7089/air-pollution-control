import os
import glob
import pickle
import json
from abc import ABC, abstractmethod
from typing import Optional, Any
from PIL import Image


class AbstractFileStorage(ABC):

    @abstractmethod
    def save(self, data: Any, file_id: str, format: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def load(self, file_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        pass

    @abstractmethod
    def list(self) -> list:
        pass


class LocalFileStorage(AbstractFileStorage):
    def __init__(self, storage_dir="storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _find_file(self, file_id: str) -> Optional[str]:
        pattern = os.path.join(self.storage_dir, f"{file_id}.*")
        matches = glob.glob(pattern)
        return matches[0] if matches else None

    def save(self, data: Any, file_id: str, format: Optional[str] = None) -> bool:
        try:
            dir_path = os.path.join(self.storage_dir, os.path.dirname(file_id))
            os.makedirs(dir_path, exist_ok=True)
            base_name = os.path.basename(file_id)

            if isinstance(data, (dict, list, tuple)):
                format = format or "txt"
                path = os.path.join(dir_path, f"{base_name}.{format}")
                with open(path, "w", encoding="utf-8") as file:
                    file.write(json.dumps(data, indent=4, ensure_ascii=False))

            elif isinstance(data, Image.Image):
                format = format or (data.format or "png").lower()
                path = os.path.join(dir_path, f"{base_name}.{format}")
                data.save(path)

            elif isinstance(data, str):
                format = format or "txt"
                path = os.path.join(dir_path, f"{base_name}.{format}")
                with open(path, "w", encoding="utf-8") as file:
                    file.write(data)

            elif isinstance(data, bytes):
                format = format or "bin"
                path = os.path.join(dir_path, f"{base_name}.{format}")
                with open(path, "wb") as file:
                    file.write(data)

            else:
                format = format or "pkl"
                path = os.path.join(dir_path, f"{base_name}.{format}")
                with open(path, "wb") as file:
                    pickle.dump(data, file)

            return True

        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def load(self, file_id: str) -> Optional[Any]:
        path = self._find_file(file_id)
        if not path:
            return None

        ext = path.split(".")[-1].lower()

        try:
            if ext in ("png", "jpg", "jpeg", "bmp", "gif", "webp"):
                return Image.open(path)

            elif ext in ("txt", "md", "csv", "json"):
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content 

            elif ext == "pkl":
                with open(path, "rb") as file:
                    return pickle.load(file)

            else:
                with open(path, "rb") as file:
                    return file.read()

        except Exception as e:
            print(f"Error loading file: {e}")
            return None

    def delete(self, file_id: str) -> bool:
        path = self._find_file(file_id)
        if path:
            os.remove(path)
            return True
        return False

    def list(self) -> list:
        files = glob.glob(os.path.join(self.storage_dir, "**/*.*"), recursive=True)
        return [os.path.relpath(f, self.storage_dir) for f in files]
