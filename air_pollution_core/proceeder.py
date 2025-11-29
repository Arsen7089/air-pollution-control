from air_pollution_core.mask import MaskGenerator
from air_pollution_core.calculator import AreaCalculator
from air_pollution_core.visualizer import ImageVisualizer
from lookup.api import AbstractAPIManager, FreeAPIManager
from db.file_storage import LocalFileStorage
from PIL import Image
from typing import Optional
import numpy as np
import cv2

class SatelliteImageProceeder:

    HSV_RANGES_ID = "smg/hsv_ranges"

    def __init__(
        self,
        trees_per_m2: float = 0.02,
        clean_air_forest_percent: float = 0.2,
    ):
        self.file_storage = LocalFileStorage()
        
        self.api = FreeAPIManager(self.file_storage)
        self.trees_per_m2 = trees_per_m2
        self.clean_air_forest_percent = clean_air_forest_percent

        hsv_ranges = self.file_storage.load_dict(self.HSV_RANGES_ID)
        if not hsv_ranges:
            forest_img = np.array(Image.open("forest_full.png").convert("HSV"))
            field_img = np.array(Image.open("field_full.png").convert("HSV"))
            hsv_ranges = {
                "trees": SatelliteImageProceeder.analyze_hsv_range(forest_img),
                "fields": SatelliteImageProceeder.analyze_hsv_range(field_img)
            }
            self.file_storage.save_dict(hsv_ranges, self.HSV_RANGES_ID)

        self.mask_generator = MaskGenerator(hsv_ranges)
        self.area_calculator = AreaCalculator()
        self.visualizer = ImageVisualizer()

    def process_by_place(self, place_name: str):
        img_hsv, pixel_m2 = self.api.get_photo_by_place(place_name)
        return self.process_satellite_image(img_hsv, pixel_m2, place_name)

    def process_satellite_image(self, img_hsv: np.ndarray, pixel_to_m2: float, place_name: str):
        forest_data_id = f"{place_name}/forest_data" 
        overlay_hsv_id = f"{place_name}/overlay_hsv"

        saved_forest_data = self.file_storage.load_dict(forest_data_id)
        saved_overlay_hsv = self.file_storage.load_numpy(overlay_hsv_id)

        if saved_forest_data is not None and saved_overlay_hsv is not None:
            overlay_rgb = cv2.cvtColor(saved_overlay_hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
            return {"image": Image.fromarray(overlay_rgb), **saved_forest_data}

        mask_trees, mask_fields = self.mask_generator.generate_masks_from_hsv(img_hsv)
        forest_data = self.area_calculator.calculate_forest_data(
            mask_trees, mask_fields, pixel_to_m2,
            trees_per_m2=self.trees_per_m2,
            clean_air_forest_percent=self.clean_air_forest_percent
        )
        overlay_hsv = self.visualizer.overlay_masks(img_hsv, mask_trees, mask_fields)
        overlay_rgb = cv2.cvtColor(overlay_hsv, cv2.COLOR_HSV2RGB)
        self.file_storage.save_dict(forest_data, forest_data_id)
        self.file_storage.save_numpy(overlay_hsv, overlay_hsv_id)

        result = {"image": Image.fromarray(overlay_rgb), **forest_data}
        return result
    
    @staticmethod
    def analyze_hsv_range(img_hsv: np.ndarray, pad=(5, 15, 15)):
        h, s, v = img_hsv[:, :, 0].ravel(), img_hsv[:, :, 1].ravel(), img_hsv[:, :, 2].ravel()
        valid_mask = v > 15
        h, s, v = h[valid_mask], s[valid_mask], v[valid_mask]
        if len(h) == 0:
                return np.array([0,0,0], dtype=np.uint8), np.array([179,255,255], dtype=np.uint8)
        low = np.array([np.percentile(h, 10), np.percentile(s, 10), np.percentile(v, 10)], dtype=np.float32)
        high = np.array([np.percentile(h, 90), np.percentile(s, 90), np.percentile(v, 90)], dtype=np.float32)
        pad = np.array(pad, dtype=np.float32)
        low -= pad
        high += pad
        low = np.clip(low, 0, 255)
        high = np.clip(high, 0, 255)
        low = np.minimum(low, high)
        return low.tolist(), high.tolist()


