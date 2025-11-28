import numpy as np
import cv2
from PIL import Image
from typing import Tuple

class MaskGenerator:
    def __init__(self, forest_img: Image.Image, field_img: Image.Image, photo_formatter):
        if forest_img is None or field_img is None:
            raise RuntimeError("Calibration images missing.")
        
        self.hsv_ranges = {
            "trees": photo_formatter.analyze_hsv_range(forest_img),
            "fields": photo_formatter.analyze_hsv_range(field_img)
        }

    def generate_masks(self, image_pil: Image.Image) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        img_rgb = np.array(image_pil.convert("RGB"))
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

        low_t, high_t = self.hsv_ranges["trees"]
        low_f, high_f = self.hsv_ranges["fields"]

        mask_trees = cv2.inRange(hsv, low_t, high_t)
        mask_fields = cv2.inRange(hsv, low_f, high_f)
        mask_fields = cv2.bitwise_and(mask_fields, cv2.bitwise_not(mask_trees))

        return mask_trees, mask_fields, img_rgb
