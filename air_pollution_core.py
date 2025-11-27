from PIL import Image
import numpy as np
import cv2
from lookup import AbstractAPIManager
import photo_formatter

class SatelliteImageProceeder:
    CLEAN_AIR_FOREST_PERCENT = 0.2

    def __init__(self, api_manager: AbstractAPIManager, forest_img: Image.Image, field_img: Image.Image, trees_per_m2: float = 0.02):
        self.api = api_manager
        self.TREES_PER_M2 = trees_per_m2

        if forest_img is None or field_img is None:
            raise RuntimeError("Calibration images missing.")

        self.hsv_ranges = {
            "trees": photo_formatter.analyze_hsv_range(forest_img),
            "fields": photo_formatter.analyze_hsv_range(field_img),
        }

    def process_by_place(self, place_name: str, debug=False):
        result = self.api.get_photo_by_place(place_name)
        if not result:
            raise ValueError(f"No image for '{place_name}'")
        if isinstance(result, tuple):
            image, pixel_m2 = result
        else:
            image = result
            pixel_m2 = 1.0
        return self.process_satellite_image(image, pixel_m2, debug)

    def process_satellite_image(self, image_pil: Image.Image, pixel_to_m2: float = 0.5, debug: bool = False):
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)

        low_t, high_t = self.hsv_ranges["trees"]
        low_f, high_f = self.hsv_ranges["fields"]

        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        mask_trees = cv2.inRange(hsv, low_t, high_t)
        mask_fields = cv2.inRange(hsv, low_f, high_f)
        mask_fields = cv2.bitwise_and(mask_fields, cv2.bitwise_not(mask_trees))

        trees_px, trees_m2, trees_ha, existing_trees = self.estimate_area_and_trees(mask_trees, pixel_to_m2)
        fields_px, fields_m2, fields_ha, _ = self.estimate_area_and_trees(mask_fields, pixel_to_m2)

        height, width = mask_trees.shape
        total_area_m2 = height * width * pixel_to_m2
        forest_percent = trees_m2 / total_area_m2 if total_area_m2 > 0 else 0

        trees_to_plant = 0
        planting_density_m2 = 0.0
        if forest_percent < self.CLEAN_AIR_FOREST_PERCENT:
            required_forest_area_m2 = total_area_m2 * self.CLEAN_AIR_FOREST_PERCENT
            trees_to_plant = max(0, int(required_forest_area_m2 * self.TREES_PER_M2 - existing_trees))
            if fields_m2 > 0:
                planting_density_m2 = trees_to_plant / fields_m2

        overlay = img_cv.copy()
        overlay[mask_fields > 0] = (0, 0, 255)
        overlay[mask_trees > 0] = (255, 0, 0)
        blended = cv2.addWeighted(img_cv, 0.75, overlay, 0.25, 0)
        result_img = Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))

        return {
            "image": result_img,
            "trees": {
                "pixels": trees_px,
                "area_m2": round(trees_m2, 2),
                "area_hectares": round(trees_ha, 4),
                "estimated_trees": int(existing_trees)
            },
            "fields": {
                "pixels": fields_px,
                "area_m2": round(fields_m2, 2),
                "area_hectares": round(fields_ha, 4)
            },
            "forest_coverage_percent": round(forest_percent * 100, 2),
            "trees_to_plant_for_clean_air": trees_to_plant,
            "planting_density_m2": round(planting_density_m2, 4)  # дерев на 1 м² поля
        }

    def estimate_area_and_trees(self, mask, pixel_to_m2):
        non_zero_pixels = np.count_nonzero(mask)
        area_m2 = non_zero_pixels * pixel_to_m2
        area_ha = area_m2 / 10_000
        trees_est = area_m2 * self.TREES_PER_M2
        return non_zero_pixels, area_m2, area_ha, trees_est
