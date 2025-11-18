from abc import ABC, abstractmethod
from PIL import Image
from typing import Dict
import numpy as np
import cv2
from lookup import AbstractAPIManager
from photo_storage import AbstractPhotoStorage
import photo_formatter


class SatelliteImageProceeder:
    def __init__(
            self,
            api_manager: AbstractAPIManager,
            photo_storage: AbstractPhotoStorage,
            forest_place: Dict = None,
            field_place: Dict = None,
            road_place: Dict = None
        ):
        self.api = api_manager
        self.photo_storage = photo_storage

        # Default test places
        forest_place = forest_place or {"name_of_place": "forest_sample", "location": {"lat": 51.2220, "lng": 30.8930}}
        field_place = field_place or {"name_of_place": "field_sample", "location": {"lat": 49.1280, "lng": 31.9100}}
        road_place = road_place or {"name_of_place": "road_sample", "location": {"lat": 50.4501, "lng": 30.5234}}

        # Try loading from storage first
        f_img = photo_storage.load("forest_full")
        fe_img = photo_storage.load("field_full")
        r_img = photo_storage.load("road_full")

        # If any is missing — fetch via API and store
        if f_img is None:
            f_img = self.api.find_photo(forest_place)
            f_img = photo_formatter.get_central_fraction(f_img)
            photo_storage.save(f_img, "forest_full")

        if fe_img is None:
            fe_img = self.api.find_photo(field_place)
            fe_img = photo_formatter.get_central_fraction(fe_img)
            photo_storage.save(fe_img, "field_full")

        if r_img is None:
            r_img = self.api.find_photo(road_place)
            r_img = photo_formatter.get_central_fraction(r_img)
            photo_storage.save(r_img, "road_full")

        # Final validation
        if f_img is None or fe_img is None or r_img is None:
            raise RuntimeError("❌ Не вдалося отримати всі калібрувальні знімки (forest/field/road).")

        # HSV calibration
        self.hsv_ranges = {
            "trees": photo_formatter.analyze_hsv_range(f_img),
            "fields": photo_formatter.analyze_hsv_range(fe_img),
            "roads": photo_formatter.analyze_hsv_range(r_img),
        }

        print("✅ Calibration completed. HSV ranges:")
        for name, (low, high) in self.hsv_ranges.items():
            print(f"  {name}: low={low.tolist()}, high={high.tolist()}")



    def process_satellite_image(self, image_pil: Image.Image, cols: int = 2, rows: int = 2,
                                debug: bool = False) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        height, width = img_cv.shape[:2]
        tile_w, tile_h = width // cols, height // rows
        processed_tiles = []

        low_trees, high_trees = self.hsv_ranges["trees"]
        low_fields, high_fields = self.hsv_ranges["fields"]
        low_roads, high_roads = self.hsv_ranges["roads"]

        for y in range(rows):
            row_tiles = []
            for x in range(cols):
                x0, y0 = x * tile_w, y * tile_h
                x1, y1 = x0 + tile_w, y0 + tile_h
                tile = img_cv[y0:y1, x0:x1]

                shifted = cv2.pyrMeanShiftFiltering(tile, 5, 20)
                hsv = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)

                mask_trees = cv2.inRange(hsv, low_trees, high_trees)
                mask_fields = cv2.inRange(hsv, low_fields, high_fields)
                mask_roads = cv2.inRange(hsv, low_roads, high_roads)

                mask_trees = cv2.GaussianBlur(mask_trees, (7, 7), 0)
                mask_fields = cv2.GaussianBlur(mask_fields, (7, 7), 0)
                mask_roads = cv2.GaussianBlur(mask_roads, (7, 7), 0)

                if debug:
                    print(f"Tile ({x},{y}): trees={np.count_nonzero(mask_trees)}, "
                          f"fields={np.count_nonzero(mask_fields)}, roads={np.count_nonzero(mask_roads)}")

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

    def process_by_place(self, place_name: str, cols=2, rows=2, debug=False) -> Image.Image:
        photo = self.api.get_photo_by_place(place_name)
        if not photo:
            raise ValueError(f"❌ Не вдалося отримати зображення для '{place_name}'")
        return self.process_satellite_image(photo, cols, rows, debug)
