from typing import Tuple
import numpy as np
from PIL import Image
import cv2

class PhotoFormatter:

    @staticmethod
    def analyze_hsv_range(image_pil: Image.Image, pad: Tuple[int,int,int]=(5,15,15)) -> Tuple[np.ndarray, np.ndarray]:
        img_rgb = np.array(image_pil.convert("RGB"))
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

        h, s, v = hsv[:, :, 0].ravel(), hsv[:, :, 1].ravel(), hsv[:, :, 2].ravel()
        valid_mask = v > 15
        h, s, v = h[valid_mask], s[valid_mask], v[valid_mask]

        if len(h) == 0:
            print("Warning: Empty or grayscale image detected.")
            return np.array([0,0,0], dtype=np.uint8), np.array([179,255,255], dtype=np.uint8)

        low = np.array([np.percentile(h, 10), np.percentile(s, 10), np.percentile(v, 10)], dtype=np.float32)
        high = np.array([np.percentile(h, 90), np.percentile(s, 90), np.percentile(v, 90)], dtype=np.float32)
        pad = np.array(pad, dtype=np.float32)

        low -= pad
        high += pad

        low = np.clip(low, 0, 255)
        high = np.clip(high, 0, 255)
        low = np.minimum(low, high)

        return low.astype(np.uint8), high.astype(np.uint8)

