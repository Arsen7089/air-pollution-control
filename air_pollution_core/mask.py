import numpy as np
import cv2
from typing import Dict, Tuple

class MaskGenerator:
    def __init__(self, hsv_ranges: Dict[str, Tuple[np.ndarray, np.ndarray]]):
        if not hsv_ranges or "trees" not in hsv_ranges or "fields" not in hsv_ranges:
            raise ValueError("hsv_ranges must contain 'trees' and 'fields'")
        
        self.hsv_ranges = {
            k: (np.array(v[0], dtype=np.uint8), np.array(v[1], dtype=np.uint8))
            for k, v in hsv_ranges.items()
        }

    def generate_masks_from_hsv(self, img_hsv: np.ndarray):
        low_t, high_t = self.hsv_ranges["trees"]
        low_f, high_f = self.hsv_ranges["fields"]

        mask_trees = cv2.inRange(img_hsv, low_t, high_t)
        mask_fields = cv2.inRange(img_hsv, low_f, high_f)
        mask_fields = cv2.bitwise_and(mask_fields, cv2.bitwise_not(mask_trees))

        return mask_trees, mask_fields


