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
    def find_photo(self, results, query=None):
        pass

    @abstractmethod
    def find_coordinates(self, place_name):
        pass

    @abstractmethod
    def find_air_pollution_index(self, results, query=None):
        pass

    def get_photo_by_place(self, place_name):
        results = self.find_coordinates(place_name)
        if not results:
            raise ValueError(f"No coordinates found for '{place_name}'")

        photo_img, pixel_area_m2 = self.find_photo(results, query=place_name)
        if photo_img is None:
            raise ValueError(
                f"No photo found for coordinates ({results['lat']}, {results['lng']})"
            )

        air_pollution_index = self.find_air_pollution_index(results, query=place_name)

        return photo_img, pixel_area_m2, air_pollution_index


class FreeAPIManager(AbstractAPIManager):
    def __init__(self, storage,
                 owm_api_key: str,
                 bbox_delta: float = 0.005,
                 img_width: int = 600,
                 img_height: int = 400):
        self.storage = storage
        self.owm_api_key = owm_api_key
        self.bbox_delta = bbox_delta
        self.img_width = img_width
        self.img_height = img_height

    def find_photo(self, results, query=None) -> Optional[Tuple[Image.Image, float]]:
        lat = results.get('lat')
        lon = results.get('lng')
        name = str(query).replace(" ", "_") if query else f"{lat}_{lon}"

        img_file_id = f"locations/{name}/photo"
        cached_img = self.storage.load_img(img_file_id)
        if isinstance(cached_img, Image.Image):
            return cached_img, self.compute_pixel_scale(lat)

        url = (
            "https://services.arcgisonline.com/arcgis/rest/services/"
            "World_Imagery/MapServer/export?"
            f"bbox={lon - self.bbox_delta},{lat - self.bbox_delta},"
            f"{lon + self.bbox_delta},{lat + self.bbox_delta}"
            f"&bboxSR=4326&size={self.img_width},{self.img_height}&f=image"
        )

        with urllib.request.urlopen(url, timeout=60) as r:
            img_data = r.read()

        img = Image.open(io.BytesIO(img_data))
        img.load()
        self.storage.save_img(img, img_file_id)

        pixel_area_m2 = self.compute_pixel_scale(lat)
        return img, pixel_area_m2

    def find_coordinates(self, query: str) -> Optional[Dict[str, Any]]:
        file_id = f"locations/{query}/coords"
        cached = self.storage.load_dict(file_id)
        if isinstance(cached, dict):
            return cached

        r = requests.get(
            "https://photon.komoot.io/api/",
            params={"q": query, "limit": 1},
            timeout=60
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("features"):
            return None

        coords = data["features"][0]["geometry"]["coordinates"]
        result = {"lat": coords[1], "lng": coords[0]}
        self.storage.save_dict(result, file_id)
        return result

    def find_air_pollution_index(self, results, query=None) -> Dict[str, Any]:
        lat = results.get('lat')
        lon = results.get('lng')
        name = str(query).replace(" ", "_") if query else f"{lat}_{lon}"
        file_id = f"locations/{name}/pollution"

        cached = self.storage.load_dict(file_id)
        if isinstance(cached, dict):
            return cached

        if not self.owm_api_key:
            raise ValueError("OpenWeather API key not set in FreeAPIManager")

        url = "https://api.openweathermap.org/data/2.5/air_pollution"
        params = {"lat": lat, "lon": lon, "appid": self.owm_api_key}
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("list"):
            raise ValueError(f"No air pollution data for {lat},{lon}")

        components = data["list"][0]["components"]
        pm25 = components.get("pm2_5", 0.0)

        def aqi_pm25(c: float) -> int:
            breakpoints = [
                (0.0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500)
            ]
            for c_low, c_high, i_low, i_high in breakpoints:
                if c_low <= c <= c_high:
                    return round((i_high - i_low)/(c_high - c_low)*(c - c_low) + i_low)
            return 500

        aqi_value = aqi_pm25(pm25)
        if aqi_value <= 50:
            category = "Good"
        elif aqi_value <= 100:
            category = "Moderate"
        elif aqi_value <= 150:
            category = "Unhealthy for Sensitive Groups"
        elif aqi_value <= 200:
            category = "Unhealthy"
        elif aqi_value <= 300:
            category = "Very Unhealthy"
        else:
            category = "Hazardous"

        result = {
            "aqi": aqi_value,
            "category": category
        }
        self.storage.save_dict(result, file_id)
        return result

    def compute_pixel_scale(self, lat: float) -> float:
        meters_per_deg = 111_320
        lat_m = self.bbox_delta * meters_per_deg
        lon_m = self.bbox_delta * meters_per_deg * math.cos(math.radians(lat))
        total_area_m2 = (2 * lat_m) * (2 * lon_m)
        return total_area_m2 / (self.img_width * self.img_height)
