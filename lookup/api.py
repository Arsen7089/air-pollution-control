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
        pm10 = components.get("pm10", 0.0)           
        co = components.get("co", 0.0) / 1145.0      
        so2 = components.get("so2", 0.0) / 2620.0   
        no2 = components.get("no2", 0.0) / 1880.0    
        o3 = components.get("o3", 0.0) / 2000.0    

        breakpoints = {
            "pm25": [
                (0.0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500)
            ],
            "pm10": [
                (0, 54, 0, 50),
                (55, 154, 51, 100),
                (155, 254, 101, 150),
                (255, 354, 151, 200),
                (355, 424, 201, 300),
                (425, 604, 301, 500)
            ],
            "co": [
                (0.0, 4.4, 0, 50),
                (4.5, 9.4, 51, 100),
                (9.5, 12.4, 101, 150),
                (12.5, 15.4, 151, 200),
                (15.5, 30.4, 201, 300),
                (30.5, 50.4, 301, 500)
            ],
            "so2": [
                (0.0, 0.035, 0, 50),
                (0.036, 0.075, 51, 100),
                (0.076, 0.185, 101, 150),
                (0.186, 0.304, 151, 200),
                (0.305, 0.604, 201, 300),
                (0.605, 1.004, 301, 500)
            ],
            "no2": [
                (0.0, 0.053, 0, 50),
                (0.054, 0.100, 51, 100),
                (0.101, 0.360, 101, 150),
                (0.361, 0.649, 151, 200),
                (0.650, 1.249, 201, 300),
                (1.250, 2.049, 301, 500)
            ],
            "o3": [
                (0.0, 0.054, 0, 50),
                (0.055, 0.070, 51, 100),
                (0.071, 0.085, 101, 150),
                (0.086, 0.105, 151, 200),
                (0.106, 0.200, 201, 300)
            ]
        }

        def calc_aqi(value, pollutant):
            for c_low, c_high, i_low, i_high in breakpoints[pollutant]:
                if c_low <= value <= c_high:
                    return round((i_high - i_low) / (c_high - c_low) * (value - c_low) + i_low)
            return 500

        aqi_values = {
            "pm25": calc_aqi(pm25, "pm25"),
            "pm10": calc_aqi(pm10, "pm10"),
            "co": calc_aqi(co, "co"),
            "so2": calc_aqi(so2, "so2"),
            "no2": calc_aqi(no2, "no2"),
            "o3": calc_aqi(o3, "o3")
        }

        aqi_value = max(aqi_values.values())

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
            "category": category,
            "components": aqi_values  
        }

        self.storage.save_dict(result, file_id)
        return result



    def compute_pixel_scale(self, lat: float) -> float:
        meters_per_deg = 111_320
        lat_m = self.bbox_delta * meters_per_deg
        lon_m = self.bbox_delta * meters_per_deg * math.cos(math.radians(lat))
        total_area_m2 = (2 * lat_m) * (2 * lon_m)
        return total_area_m2 / (self.img_width * self.img_height)
