from PIL import Image
import numpy as np
import cv2

class ImageVisualizer:
    @staticmethod
    def overlay_masks(img_hsv: np.ndarray, mask_trees: np.ndarray, mask_fields: np.ndarray, alpha: float = 0.5) -> Image.Image:
        img_rgb = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB)
        overlay = img_rgb.copy()
        overlay[mask_fields > 0] = (0, 0, 255)
        overlay[mask_trees > 0] = (255, 0, 0)
        blended = cv2.addWeighted(img_rgb, 0.75, overlay, 0.25, 0)
        result_img = Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))
        return result_img




