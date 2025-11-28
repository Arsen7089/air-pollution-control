from air_pollution_core.mask import MaskGenerator
from air_pollution_core.calculator import AreaCalculator
from air_pollution_core.visualizer import ImageVisualizer
from air_pollution_core.photo_formatter import PhotoFormatter
from lookup.api import AbstractAPIManager, FreeAPIManager
from db.file_storage import LocalFileStorage, AbstractFileStorage
from PIL import Image
from typing import Optional

class SatelliteImageProceeder:

    def __init__(
        self,
        trees_per_m2: float = 0.02,
        clean_air_forest_percent: float = 0.2,
    ):
        self.file_storage = LocalFileStorage()
        forest_img = self.file_storage.load("forest_full")
        field_img = self.file_storage.load("field_full")
        self.api = FreeAPIManager(self.file_storage)
        self.trees_per_m2 = trees_per_m2
        self.clean_air_forest_percent = clean_air_forest_percent
        photo_formatter = PhotoFormatter()
        self.mask_generator = MaskGenerator(forest_img, field_img, photo_formatter=photo_formatter)
        self.area_calculator = AreaCalculator()
        self.visualizer = ImageVisualizer()

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
        mask_trees, mask_fields, img_rgb = self.mask_generator.generate_masks(image_pil)
        forest_data = self.area_calculator.calculate_forest_data(
            mask_trees, mask_fields, pixel_to_m2,
            trees_per_m2=self.trees_per_m2,
            clean_air_forest_percent=self.clean_air_forest_percent
        )
        result_img = self.visualizer.overlay_masks(img_rgb, mask_trees, mask_fields)
        return {"image": result_img, **forest_data}
