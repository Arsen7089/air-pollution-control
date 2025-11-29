import cv2
from PIL import Image
import numpy as np

class ImageVisualizer:

    @staticmethod
    def overlay_masks(img_hsv: np.ndarray, mask_trees: np.ndarray, mask_fields: np.ndarray) -> np.ndarray:
        overlay = img_hsv.copy()
        red_hsv = np.array([0, 255, 255], dtype=np.uint8)
        blue_hsv = np.array([120, 255, 255], dtype=np.uint8)
        overlay[mask_fields > 0] = red_hsv
        overlay[mask_trees > 0] = blue_hsv
        return overlay

