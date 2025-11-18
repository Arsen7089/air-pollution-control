from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image
import os

class AbstractPhotoStorage(ABC):

    @abstractmethod
    def save(self, image: Image.Image, image_id: str) -> bool:
        pass

    @abstractmethod
    def load(self, image_id: str) -> Optional[Image.Image]:
        pass

    @abstractmethod
    def delete(self, image_id: str) -> bool:
        pass
    
    @abstractmethod
    def list(self) -> list:
        pass

class LocalPhotoStorage(AbstractPhotoStorage):
    def __init__(self, storage_dir="photos"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save(self, image: Image.Image, image_id: str) -> bool:
        path = os.path.join(self.storage_dir, f"{image_id}.png")
        try:
            image.save(path, format="PNG")
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    def load(self, image_id: str) -> Optional[Image.Image]:
        path = os.path.join(self.storage_dir, f"{image_id}.png")
        if os.path.exists(path):
            return Image.open(path)
        return None

    def delete(self, image_id: str) -> bool:
        path = os.path.join(self.storage_dir, f"{image_id}.png")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list(self) -> list:
        return [f.split(".")[0] for f in os.listdir(self.storage_dir) if f.endswith(".png")]

