from abc import ABC, abstractmethod
from typing import Tuple, Dict, Optional
from PIL import Image
import numpy as np
import cv2
from lookup import AbstractAPIManager


class SatelliteImageProceeder:
    def __init__(self, api_manager: AbstractAPIManager,
                 forest_place: Dict = None,
                 field_place: Dict = None,
                 road_place: Dict = None):
        """
        api_manager: об'єкт, що реалізує AbstractAPIManager
        forest_place, field_place, road_place: словники формату
            {"name_of_place": name, "location": {"lat":..., "lng":...}}

        Якщо не вказані — будуть використані дефолтні приклади.
        Під час ініціалізації викликаються api_manager.find_photo(place_dict)
        для кожної контрольної зони, і визначаються HSV-діапазони.
        """
        self.api = api_manager

        # --- Дефолтні координати контрольних зон (можна замінити своїми)
        if forest_place is None:
            forest_place = {"name_of_place": "forest_sample", "location": {"lat": 51.2220, "lng": 30.8930}}  # ліс
        if field_place is None:
            field_place = {"name_of_place": "field_sample", "location": {"lat": 49.1280, "lng": 31.9100}}   # поле
        if road_place is None:
            road_place = {"name_of_place": "road_sample", "location": {"lat": 50.4501, "lng": 30.5234}}     # дорога

        print("🔎 Requesting calibration images using API.find_photo(...)")
        f_img = self.api.find_photo(forest_place)
        fe_img = self.api.find_photo(field_place)
        r_img = self.api.find_photo(road_place)
        
        f_img = self._get_central_fraction(f_img)
        fe_img = self._get_central_fraction(fe_img)
        r_img = self._get_central_fraction(r_img)
        
        f_img.save("forest_full.png")
        fe_img.save("field_full.png")
        r_img.save("road_full.png")

        if f_img is None or fe_img is None or r_img is None:
            raise RuntimeError("❌ Не вдалося отримати всі калібрувальні знімки (forest/field/road).")

        # --- Калібрування HSV для кожного типу місцевості ---
        self.hsv_ranges = {
            "trees": self._analyze_hsv_range(f_img),
            "fields": self._analyze_hsv_range(fe_img),
            "roads": self._analyze_hsv_range(r_img),
        }

        print("✅ Calibration completed. HSV ranges:")
        for k, (low, high) in self.hsv_ranges.items():
            print(f"  {k}: low={low.tolist()}, high={high.tolist()}")

    # ----------------------------------------------------------------------
    # Аналіз HSV діапазонів
    # ----------------------------------------------------------------------
    def _analyze_hsv_range(self, image_pil: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
        """Повертає (low, high) масиви uint8 для cv2.inRange (H,S,V)."""
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[:, :, 0].ravel(), hsv[:, :, 1].ravel(), hsv[:, :, 2].ravel()

        # Ігноруємо "мертві" пікселі з V<15
        valid_mask = v > 15
        h, s, v = h[valid_mask], s[valid_mask], v[valid_mask]

        if len(h) == 0:
            print("⚠️ Warning: Empty or grayscale image detected.")
            return np.array([0, 0, 0], dtype=np.uint8), np.array([179, 255, 255], dtype=np.uint8)

        # Виключаємо екстремальні шуми — 5-й і 95-й перцентилі
        low = np.array([np.percentile(h, 5), np.percentile(s, 5), np.percentile(v, 5)], dtype=np.uint8)
        high = np.array([np.percentile(h, 95), np.percentile(s, 95), np.percentile(v, 95)], dtype=np.uint8)

        # Розширювальна "подушка", щоб не втратити частину відтінків
        pad = np.array([3, 10, 10], dtype=np.uint8)
        low = np.clip(low - pad, 0, 255)
        high = np.clip(high + pad, 0, 255)

        return low, high
    
    def _get_central_fraction(self, image_pil: Image.Image, fraction: float = 0.1) -> Image.Image:
        if not (0 < fraction <= 1):
            raise ValueError("fraction має бути в межах (0, 1].")

        # Гарантовано RGB, щоб уникнути втрати кольору
        image_pil = image_pil.convert("RGB")

        img_cv = np.array(image_pil)
        h, w = img_cv.shape[:2]

        crop_h = max(1, int(h * fraction))
        crop_w = max(1, int(w * fraction))

        y0 = h // 2 - crop_h // 2
        x0 = w // 2 - crop_w // 2

        cropped = img_cv[y0:y0 + crop_h, x0:x0 + crop_w]

        # Повертаємо знову як RGB
        return Image.fromarray(cropped, mode="RGB")


    def process_satellite_image(self, image_pil: Image.Image, cols: int = 2, rows: int = 2,
                                debug: bool = False) -> Image.Image:
        """
        Розбиває зображення на tiles, фільтрує за HSV і накладає кольорові маски.
        - Ліс (trees): синій
        - Поля (fields): червоний
        - Дороги (roads): жовтий
        """
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        height, width = img_cv.shape[:2]
        tile_w, tile_h = width // cols, height // rows
        processed_tiles = []

        # Розпаковуємо HSV діапазони
        low_trees, high_trees = self.hsv_ranges["trees"]
        low_fields, high_fields = self.hsv_ranges["fields"]
        low_roads, high_roads = self.hsv_ranges["roads"]

        for y in range(rows):
            row_tiles = []
            for x in range(cols):
                x0, y0 = x * tile_w, y * tile_h
                x1, y1 = x0 + tile_w, y0 + tile_h
                tile = img_cv[y0:y1, x0:x1]

                # MeanShift фільтрація для зменшення шуму
                shifted = cv2.pyrMeanShiftFiltering(tile, 5, 20)
                hsv = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)

                # Маски
                mask_trees = cv2.inRange(hsv, low_trees, high_trees)
                mask_fields = cv2.inRange(hsv, low_fields, high_fields)
                mask_roads = cv2.inRange(hsv, low_roads, high_roads)

                # Згладжування
                mask_trees = cv2.GaussianBlur(mask_trees, (7, 7), 0)
                mask_fields = cv2.GaussianBlur(mask_fields, (7, 7), 0)
                mask_roads = cv2.GaussianBlur(mask_roads, (7, 7), 0)

                if debug:
                    print(f"Tile ({x},{y}): trees={np.count_nonzero(mask_trees)}, "
                          f"fields={np.count_nonzero(mask_fields)}, roads={np.count_nonzero(mask_roads)}")

                # Накладання кольорів
                color_overlay = tile.copy()
                color_overlay[mask_roads > 0]  = (0, 255, 255)
                color_overlay[mask_trees > 0]  = (255, 0, 0)
                color_overlay[mask_fields > 0] = (0, 0, 255)


                blended = cv2.addWeighted(tile, 0.8, color_overlay, 0.2, 0)
                row_tiles.append(blended)

            processed_row = np.hstack(row_tiles)
            processed_tiles.append(processed_row)

        combined = np.vstack(processed_tiles)
        return Image.fromarray(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))

    # ----------------------------------------------------------------------
    # Отримання знімку за назвою місця (через API)
    # ----------------------------------------------------------------------
    def process_by_place(self, place_name: str, cols=2, rows=2, debug=False) -> Image.Image:
        """Отримує супутникове фото для місця через API і обробляє його."""
        photo = self.api.get_photo_by_place(place_name)
        if not photo:
            raise ValueError(f"❌ Не вдалося отримати зображення для '{place_name}'")
        return self.process_satellite_image(photo, cols, rows, debug)

    # ----------------------------------------------------------------------
    # Повертає знайдені HSV-діапазони
    # ----------------------------------------------------------------------
    def get_hsv_ranges(self) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        return self.hsv_ranges
