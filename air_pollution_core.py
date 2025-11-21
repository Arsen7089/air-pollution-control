from abc import ABC, abstractmethod
from PIL import Image
from typing import Dict, Any
import numpy as np
import cv2
from lookup import AbstractAPIManager
from file_storage import AbstractFileStorage  
import photo_formatter


class SatelliteImageProceeder:
    def __init__(
        self,
        api_manager: AbstractAPIManager,
        file_storage: AbstractFileStorage,   
        forest_place: Dict = None,
        field_place: Dict = None,
        road_place: Dict = None
    ):
        self.api = api_manager
        self.storage = file_storage

        forest_place = forest_place or {"name_of_place": "forest_sample", "location": {"lat": 51.2220, "lng": 30.8930}}
        field_place = field_place or {"name_of_place": "field_sample", "location": {"lat": 49.1280, "lng": 31.9100}}
        road_place = road_place or {"name_of_place": "road_sample", "location": {"lat": 50.4501, "lng": 30.5234}}

        self.hsv_ranges = self.storage.load("hsv_ranges")
        
        if not self.hsv_ranges:  
            print("🔍 HSV ranges not found. Generating calibration images...")

            forest_img = self.storage.load("forest_full")
            if forest_img is None:
                forest_img = photo_formatter.get_central_fraction(
                    self.api.find_photo(forest_place)
                )
                self.storage.save(forest_img, "forest_full")

            field_img = self.storage.load("field_full")
            if field_img is None:
                field_img = photo_formatter.get_central_fraction(
                    self.api.find_photo(field_place)
                )
                self.storage.save(field_img, "field_full")

            road_img = self.storage.load("road_full")
            if road_img is None:
                road_img = photo_formatter.get_central_fraction(
                    self.api.find_photo(road_place)
                )
                self.storage.save(road_img, "road_full")

            if forest_img is None or field_img is None or road_img is None:
                raise RuntimeError("Calibration images missing (forest/field/road).")

            self.hsv_ranges = {
                "trees": photo_formatter.analyze_hsv_range(forest_img),
                "fields": photo_formatter.analyze_hsv_range(field_img),
                "roads": photo_formatter.analyze_hsv_range(road_img),
            }
            
            self.storage.save(self.hsv_ranges, "hsv_ranges")
            print("💾 HSV ranges saved to storage.")

        print("✅ Calibration Completed. HSV ranges:")
        for name, (low, high) in self.hsv_ranges.items():
            print(f"  {name}: low={low.tolist()}, high={high.tolist()}")

    def process_satellite_image(self, image_pil: Image.Image, cols: int = 2, rows: int = 2, debug: bool = False) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        height, width = img_cv.shape[:2]
        tile_w, tile_h = width // cols, height // rows

        processed_rows = []
        low_t, high_t = self.hsv_ranges["trees"]
        low_f, high_f = self.hsv_ranges["fields"]
        low_r, high_r = self.hsv_ranges["roads"]

        for y in range(rows):
            row_tiles = []
            for x in range(cols):
                tile = img_cv[y*tile_h:(y+1)*tile_h, x*tile_w:(x+1)*tile_w]

                shifted = cv2.pyrMeanShiftFiltering(tile, 5, 20)
                hsv = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)

                mask_trees = cv2.inRange(hsv, low_t, high_t)
                mask_fields = cv2.inRange(hsv, low_f, high_f)
                mask_roads = cv2.inRange(hsv, low_r, high_r)

                if debug:
                    print(f"Tile ({x},{y}): trees={np.count_nonzero(mask_trees)}, "
                          f"fields={np.count_nonzero(mask_fields)}, "
                          f"roads={np.count_nonzero(mask_roads)}")

                overlay = tile.copy()
                overlay[mask_roads > 0] = (0, 255, 255)
                overlay[mask_trees > 0] = (255, 0, 0)
                overlay[mask_fields > 0] = (0, 0, 255)

                blended = cv2.addWeighted(tile, 0.8, overlay, 0.2, 0)
                row_tiles.append(blended)

            processed_rows.append(np.hstack(row_tiles))

        combined = np.vstack(processed_rows)
        return Image.fromarray(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))

    def process_by_place(self, place_name: str, cols=2, rows=2, debug=False) -> Image.Image:
        photo = self.api.get_photo_by_place(place_name)
        if not photo:
            raise ValueError(f"❌ No image available for '{place_name}'")
        return self.process_satellite_image(photo, cols, rows, debug)

