import urllib.request
import requests
import urllib.error
import io
from PIL import Image
from abc import ABC, abstractmethod

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
    def find_photo(self, results):
        try:
            lat = results['location']['lat']
            lon = results['location']['lng']
        except KeyError as e:
            print(f"❌ Помилка: відсутній ключ у results — {e}")
            return None

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
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP помилка: {e.code} — {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"❌ Помилка з’єднання: {e.reason}")
            return None
        except Exception as e:
            print(f"❌ Невідома помилка при завантаженні: {e}")
            return None

        try:
            img = Image.open(io.BytesIO(data))
            img.load()  # перевірка, чи дійсно це зображення
            print("✅ Зображення успішно завантажено!")
            return img
        except Exception as e:
            print(f"❌ Помилка при відкритті зображення: {e}")
            return None


    def find_coordinates(self, query):
        import requests

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
            print(f"✅ Знайдено: {name}")
            return {"name_of_place": name, "location": {"lat": coords[1], "lng": coords[0]}}

        except Exception as e:
            print(f"❌ Помилка запиту: {e}")
            return None
    
