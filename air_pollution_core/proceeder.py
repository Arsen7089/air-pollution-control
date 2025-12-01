from air_pollution_core.mask import MaskGenerator
from air_pollution_core.calculator import AreaCalculator
from air_pollution_core.visualizer import ImageVisualizer
from lookup.api import AbstractAPIManager, FreeAPIManager
from db.file_storage import LocalFileStorage
from db.mongo.mongo_storage import MongoFileStorage
from PIL import Image
import numpy as np
import cv2

class SatelliteImageProceeder:

    HSV_RANGES_ID = "calibration/simple_mask/hsv_ranges"

    def __init__(
        self,
        trees_per_m2: float = 0.02,
        clean_air_forest_percent: float = 0.2,
    ):
        self.file_storage = MongoFileStorage()
        self.api = FreeAPIManager(self.file_storage)
        self.trees_per_m2 = trees_per_m2
        self.clean_air_forest_percent = clean_air_forest_percent

        hsv_ranges = self.file_storage.load_dict(self.HSV_RANGES_ID)
        if not hsv_ranges:
            forest_img = self.to_hsv_np(Image.open("forest_full.png"))
            field_img = self.to_hsv_np(Image.open("field_full.png"))
            hsv_ranges = {
                "trees": self.analyze_hsv_range(forest_img),
                "fields": self.analyze_hsv_range(field_img)
            }
            self.file_storage.save_dict(hsv_ranges, self.HSV_RANGES_ID)

        self.mask_generator = MaskGenerator(hsv_ranges)
        self.area_calculator = AreaCalculator()
        self.visualizer = ImageVisualizer()

    def to_hsv_np(self, image_pil: Image.Image) -> np.ndarray:
        """Convert PIL image to HSV NumPy array (single conversion)."""
        rgb = np.asarray(image_pil.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    def process_by_place(self, place_name: str):
        img, pixel_m2 = self.api.get_photo_by_place(place_name)
        return self.process_satellite_image(img, pixel_m2, place_name)

    def process_satellite_image(self, img: Image.Image, pixel_to_m2: float, place_name: str):
        forest_data_id = f"locations/{place_name}/forest_data"
        overlay_id = f"locations/{place_name}/overlay"

        saved_forest_data = self.file_storage.load_dict(forest_data_id)
        saved_overlay = self.file_storage.load_img(overlay_id)

        if saved_forest_data is not None and saved_overlay is not None:
            return {"image": saved_overlay, **saved_forest_data}

        img_hsv = self.to_hsv_np(img)
        mask_trees, mask_fields = self.mask_generator.generate_masks_from_hsv(img_hsv)

        forest_data = self.area_calculator.calculate_forest_data(
            mask_trees, mask_fields, pixel_to_m2,
            trees_per_m2=self.trees_per_m2,
            clean_air_forest_percent=self.clean_air_forest_percent
        )

        overlay = self.visualizer.overlay_masks(img_hsv, mask_trees, mask_fields)
        self.file_storage.save_dict(forest_data, forest_data_id)
        self.file_storage.save_img(overlay, overlay_id)

        return {"image": overlay, **forest_data}

    @staticmethod
    def analyze_hsv_range(img_hsv: np.ndarray, pad=(5, 15, 15)):
        h = img_hsv[..., 0]
        s = img_hsv[..., 1]
        v = img_hsv[..., 2]

        valid_mask = v > 15
        h, s, v = h[valid_mask], s[valid_mask], v[valid_mask]

        if len(h) == 0:
            raise ValueError("Invalid Image: no valid pixels found")

        low = np.percentile([h, s, v], 10, axis=1)
        high = np.percentile([h, s, v], 90, axis=1)

        low = np.clip(low - pad, 0, [255, 255, 255])
        high = np.clip(high + pad, 0, [255, 255, 255])
        low = np.minimum(low, high)

        return low.tolist(), high.tolist()