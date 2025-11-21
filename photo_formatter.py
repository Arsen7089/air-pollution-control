from PIL import Image
from typing import Tuple
import numpy as np
import cv2

def get_central_fraction(image_pil: Image.Image, fraction: float = 0.1) -> Image.Image:
        if not (0 < fraction <= 1):
            raise ValueError("fraction має бути в межах (0, 1].")
        image_pil = image_pil.convert("RGB")
        img_cv = np.array(image_pil)
        h, w = img_cv.shape[:2]
        crop_h = max(1, int(h * fraction))
        crop_w = max(1, int(w * fraction))
        y0 = h // 2 - crop_h // 2
        x0 = w // 2 - crop_w // 2
        cropped = img_cv[y0:y0 + crop_h, x0:x0 + crop_w]
        return Image.fromarray(cropped, mode="RGB")
    
def analyze_hsv_range(image_pil: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[:, :, 0].ravel(), hsv[:, :, 1].ravel(), hsv[:, :, 2].ravel()

        valid_mask = v > 15
        h, s, v = h[valid_mask], s[valid_mask], v[valid_mask]

        if len(h) == 0:
            print("Warning: Empty or grayscale image detected.")
            return np.array([0, 0, 0], dtype=np.uint8), np.array([179, 255, 255], dtype=np.uint8)

        low = np.array([np.percentile(h, 25), np.percentile(s, 25), np.percentile(v, 25)], dtype=np.uint8)
        high = np.array([np.percentile(h, 75), np.percentile(s, 75), np.percentile(v, 75)], dtype=np.uint8)

        pad = np.array([3, 10, 10], dtype=np.uint8)
        low = np.clip(low - pad, 0, 255)
        high = np.clip(high + pad, 0, 255)

        return low, high