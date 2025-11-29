import requests
import urllib.request
import io
import math
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from PIL import Image


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
            raise ValueError(f"No coordinates found for '{place_name}'")

        photo_hsv, pixel_area_m2 = self.find_photo(results)
        if photo_hsv is None:
            raise ValueError(
                f"No photo found for coordinates "
                f"({results['location']['lat']}, {results['location']['lng']})"
            )
        return photo_hsv, pixel_area_m2


class FreeAPIManager(AbstractAPIManager):
    def __init__(self, storage,
                 bbox_delta: float = 0.005,
                 img_width: int = 600,
                 img_height: int = 400):
        self.storage = storage
        self.bbox_delta = bbox_delta
        self.img_width = img_width
        self.img_height = img_height

    def find_photo(self, results) -> Optional[Tuple[np.ndarray, float]]:
        try:
            lat = results['location']['lat']
            lon = results['location']['lng']
            name = results['name_of_place']
        except KeyError:
            return None

        hsv_file_id = f"{name}/photo_hsv"

        cached_hsv = self.storage.load_numpy(hsv_file_id)
        if isinstance(cached_hsv, np.ndarray):
            return cached_hsv, self.compute_pixel_scale(lat)

        url = (
            "https://services.arcgisonline.com/arcgis/rest/services/"
            "World_Imagery/MapServer/export?"
            f"bbox={lon - self.bbox_delta},{lat - self.bbox_delta},"
            f"{lon + self.bbox_delta},{lat + self.bbox_delta}"
            f"&bboxSR=4326&size={self.img_width},{self.img_height}&f=image"
        )

        with urllib.request.urlopen(url, timeout=30) as r:
            img_data = r.read()
                

        img = Image.open(io.BytesIO(img_data))
        img.load()
        hsv_img = np.array(img.convert("HSV"))  
        self.storage.save_numpy(hsv_img, hsv_file_id)

        pixel_area_m2 = self.compute_pixel_scale(lat)
        return hsv_img, pixel_area_m2

    def find_coordinates(self, query: str) -> Optional[Dict[str, Any]]:
        file_id = f"{query}/coords"
        cached = self.storage.load_dict(file_id)

        if isinstance(cached, dict):
            return cached
        
        r = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": query, "limit": 1},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        if not data.get("features"):
            return None

        coords = data["features"][0]["geometry"]["coordinates"]

        result = {
            "name_of_place": query,
            "location": {"lat": coords[1], "lng": coords[0]},
        }

        self.storage.save_dict(result, file_id)
        return result

    def compute_pixel_scale(self, lat: float) -> float:
        meters_per_deg = 111_320
        lat_m = self.bbox_delta * meters_per_deg
        lon_m = self.bbox_delta * meters_per_deg * math.cos(math.radians(lat))

        total_area_m2 = (2 * lat_m) * (2 * lon_m)
        return total_area_m2 / (self.img_width * self.img_height)
