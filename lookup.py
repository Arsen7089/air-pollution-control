import urllib.request
import requests
import urllib.error
import io
from PIL import Image
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from file_storage import AbstractFileStorage

class AbstractAPIManager(ABC):
    @abstractmethod
    def find_photo(self, data):
        pass

    @abstractmethod
    def find_coordinates(self, place_name):
        pass

    def get_photo_by_place(self, place_name):
        results = self.find_coordinates(place_name)
        if not results:
            raise ValueError(f"Не знайдено координати для '{place_name}'")

        photo = self.find_photo(results)
        if not photo:
            raise ValueError(f"Не знайдено фото для координат ({lat}, {lon})")

        return photo


class FreeAPIManager(AbstractAPIManager):
    def __init__(self, storage: AbstractFileStorage):
        self.storage = storage  # 📦 додано storage для кешу

    def find_photo(self, results) -> Optional[Image.Image]:
        try:
            lat = results['location']['lat']
            lon = results['location']['lng']
        except KeyError as e:
            print(f"❌ Помилка: відсутній ключ у results — {e}")
            return None

        # 📌 Унікальний ID для збереження фото
        file_id = f"photo_{lat}_{lon}"

        # 🔍 Перевірка кешу
        cached_photo = self.storage.load(file_id)
        if isinstance(cached_photo, Image.Image):
            print("📸 Завантажено з кешу!")
            return cached_photo

        # 🛰 Якщо фото немає — завантажуємо з API
        url = (
            f"https://services.arcgisonline.com/arcgis/rest/services/"
            f"World_Imagery/MapServer/export?"
            f"bbox={lon-0.005},{lat-0.005},{lon+0.005},{lat+0.005}"
            f"&bboxSR=4326&size=600,400&f=image"
        )

        print("📡 Завантаження зображення з ArcGIS...")

        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = r.read()
        except Exception as e:
            print(f"❌ Помилка при завантаженні: {e}")
            return None

        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            print("✅ Зображення успішно завантажено!")

            # 💾 Зберігаємо в кеш
            self.storage.save(img, file_id)
            return img

        except Exception as e:
            print(f"❌ Помилка при відкритті зображення: {e}")
            return None


    def find_coordinates(self, query: str) -> Optional[Dict[str, Any]]:
        # 📌 Унікальний ID для координат
        file_id = f"coords_{query.replace(' ', '_').lower()}"

        # 🔍 Перевірка кешу
        cached = self.storage.load(file_id)
        if isinstance(cached, dict):
            print("📍 Координати завантажено з кешу!")
            return cached

        base_url = "https://photon.komoot.io/api/"
        params = {"q": query, "limit": 1}

        try:
            r = requests.get(base_url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()

            if not data["features"]:
                print("ℹ️ Не знайдено результатів.")
                return None

            coords = data["features"][0]["geometry"]["coordinates"]
            name = data["features"][0]["properties"]["name"]

            result = {
                "name_of_place": name,
                "location": {"lat": coords[1], "lng": coords[0]}
            }

            print(f"✅ Знайдено: {name}")

            # 💾 Зберегти в кеш (pickle)
            self.storage.save(result, file_id)
            return result

        except Exception as e:
            print(f"❌ Помилка запиту: {e}")
            return None

    
