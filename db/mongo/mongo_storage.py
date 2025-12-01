from typing import Optional
from PIL import Image
import io
from db.file_storage import AbstractFileStorage
from db.mongo.crud import MongoCRUD


class MongoFileStorage(AbstractFileStorage):
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="file_storage"):
        self.crud = MongoCRUD(mongo_uri, db_name)

    def _parse_id(self, file_id: str):
        try:
            collection, document, field = file_id.split("/", 3)
            return collection, document, field
        except ValueError:
            raise ValueError("file_id must be in format 'collection/document/field'")

    def save_dict(self, data: dict, file_id: str) -> bool:
        try:
            collection, document, field = self._parse_id(file_id)
            self.crud.update_field(collection, document, field, data)
            return True
        except Exception as e:
            print(f"Error saving dict: {e}")
            return False

    def load_dict(self, file_id: str) -> Optional[dict]:
        try:
            collection, document, field = self._parse_id(file_id)
            doc = self.crud.find_by_name(collection, document, {field: 1})
            return doc.get(field) if doc and field in doc else None
        except Exception as e:
            print(f"Error loading dict: {e}")
            return None

    def save_img(self, img: Image.Image, file_id: str) -> bool:
        try:
            collection, document, field = self._parse_id(file_id)

            img_bytes_io = io.BytesIO()
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(img_bytes_io, format="JPEG")
            img_bytes = img_bytes_io.getvalue()

            file_ref = self.crud.insert_file_binary(img_bytes)

            self.crud.update_field(collection, document, field, file_ref)
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    def load_img(self, file_id: str) -> Optional[Image.Image]:
        try:
            collection, document, field = self._parse_id(file_id)

            doc = self.crud.find_by_name(collection, document, {field: 1})
            if not doc or field not in doc:
                return None

            file_bytes = self.crud.load_file_binary(doc[field])
            return Image.open(io.BytesIO(file_bytes)) if file_bytes else None

        except Exception as e:
            print(f"Error loading image: {e}")
            return None
