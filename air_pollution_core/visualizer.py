import cv2
from PIL import Image
import numpy as np

class ImageVisualizer:

    @staticmethod
    def overlay_masks(img_rgb: np.ndarray, mask_trees: np.ndarray, mask_fields: np.ndarray) -> Image.Image:
        overlay = img_rgb.copy()
        overlay[mask_fields > 0] = (255, 0, 0)   # fields → red
        overlay[mask_trees > 0] = (0, 0, 255)    # trees → blue
        blended = cv2.addWeighted(img_rgb, 0.75, overlay, 0.25, 0)
        return Image.fromarray(blended)
