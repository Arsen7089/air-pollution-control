import urllib.request
import requests
import urllib.error
import io
from PIL import Image
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from file_storage import AbstractFileStorage
import math

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

        photo, pixel_area_m2 = self.find_photo(results)
        if not photo:
            raise ValueError(f"Не знайдено фото для координат ({results['location']['lat']}, {results['location']['lng']})")

        return photo, pixel_area_m2


class FreeAPIManager(AbstractAPIManager):
    def __init__(self, storage: AbstractFileStorage, bbox_delta: float = 0.005, img_width: int = 600, img_height: int = 400):
        self.storage = storage
        self.bbox_delta = bbox_delta
        self.img_width = img_width
        self.img_height = img_height

    def find_photo(self, results) -> Optional[tuple]:
        try:
            lat = results['location']['lat']
            lon = results['location']['lng']
        except KeyError as e:
            print(f"Помилка: відсутній ключ у results — {e}")
            return None

        file_id = f"photo_{lat}_{lon}"
        cached_photo = self.storage.load(file_id)
        if isinstance(cached_photo, Image.Image):
            pixel_area_m2 = self.compute_pixel_scale(lat)
            return cached_photo, pixel_area_m2

        url = (
            f"https://services.arcgisonline.com/arcgis/rest/services/"
            f"World_Imagery/MapServer/export?"
            f"bbox={lon-self.bbox_delta},{lat-self.bbox_delta},{lon+self.bbox_delta},{lat+self.bbox_delta}"
            f"&bboxSR=4326&size={self.img_width},{self.img_height}&f=image"
        )

        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = r.read()
        except Exception as e:
            print(f"Помилка при завантаженні: {e}")
            return None

        try:
            img = Image.open(io.BytesIO(data))
            img.load()
            self.storage.save(img, file_id)
            pixel_area_m2 = self.compute_pixel_scale(lat)
            return img, pixel_area_m2
        except Exception as e:
            print(f"Помилка при відкритті зображення: {e}")
            return None

    def find_coordinates(self, query: str) -> Optional[Dict[str, Any]]:
        file_id = f"coords_{query.replace(' ', '_').lower()}"
        cached = self.storage.load(file_id)
        if isinstance(cached, dict):
            return cached

        base_url = "https://photon.komoot.io/api/"
        params = {"q": query, "limit": 1}

        try:
            r = requests.get(base_url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data["features"]:
                return None

            coords = data["features"][0]["geometry"]["coordinates"]
            name = data["features"][0]["properties"]["name"]

            result = {
                "name_of_place": name,
                "location": {"lat": coords[1], "lng": coords[0]}
            }

            self.storage.save(result, file_id)
            return result

        except Exception as e:
            print(f"Помилка запиту: {e}")
            return None

    def compute_pixel_scale(self, lat: float) -> float:
        lat_m = self.bbox_delta * 111_320
        lon_m = self.bbox_delta * 111_320 * math.cos(math.radians(lat))
        area_m2 = (2*lat_m) * (2*lon_m)
        pixel_area_m2 = area_m2 / (self.img_width * self.img_height)
        return pixel_area_m2
