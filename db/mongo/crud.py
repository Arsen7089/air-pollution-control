from pymongo import MongoClient
from typing import Optional, Any
from bson.binary import Binary
from bson import ObjectId

class MongoCRUD:
    def __init__(self, mongo_uri="mongodb://localhost:27017", db_name="file_storage"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

    def get_collection(self, collection: str):
        return self.db[collection]

    def find_by_name(self, collection: str, name: str, projection: Optional[dict] = None):
        return self.db[collection].find_one({"name": name}, projection)

    def update_field(self, collection: str, name: str, field: str, value: Any):
        self.db[collection].update_one(
            {"name": name},
            {
                "$set": {field: value},
                "$setOnInsert": {"name": name}
            },
            upsert=True
        )

    def insert_file_binary(self, file_bytes: bytes) -> Any:
        files_collection = self.db["__files__"]
        return files_collection.insert_one({"file_data": Binary(file_bytes)}).inserted_id

    def load_file_binary(self, file_id) -> Optional[bytes]:
        files_collection = self.db["__files__"]
        file_doc = files_collection.find_one({"_id": file_id})
        return file_doc.get("file_data") if file_doc else None

    def delete_field(self, collection: str, name: str, field: str) -> bool:
        result = self.db[collection].update_one(
            {"name": name},
            {"$unset": {field: ""}}
        )
        return result.modified_count > 0

    def delete_document(self, collection: str, name: str) -> bool:
        result = self.db[collection].delete_one({"name": name})
        return result.deleted_count > 0

    def delete_file_binary(self, file_id) -> bool:
        files_collection = self.db["__files__"]
        result = files_collection.delete_one({"_id": file_id})
        return result.deleted_count > 0
    
    def is_file_ref(self, value: Any) -> bool:
        if not isinstance(value, ObjectId):
            return False
        files_collection = self.db["__files__"]
        return files_collection.find_one({"_id": value}) is not None

