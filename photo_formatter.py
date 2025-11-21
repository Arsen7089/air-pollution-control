from typing import Tuple
import numpy as np
from PIL import Image
import cv2

def analyze_hsv_range(image_pil: Image.Image, pad: Tuple[int,int,int]=(5,15,15)) -> Tuple[np.ndarray, np.ndarray]:
    """
    Аналізує діапазон HSV для зображення, повертає low і high, гарантуючи low <= high.
    pad: додатковий запас для каналів H, S, V
    """
    # Конвертуємо в BGR для OpenCV
    img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)

    h, s, v = hsv[:, :, 0].ravel(), hsv[:, :, 1].ravel(), hsv[:, :, 2].ravel()

    # Фільтруємо надто темні пікселі
    valid_mask = v > 15
    h, s, v = h[valid_mask], s[valid_mask], v[valid_mask]

    if len(h) == 0:
        print("Warning: Empty or grayscale image detected.")
        return np.array([0,0,0], dtype=np.uint8), np.array([179,255,255], dtype=np.uint8)

    # Беремо 10-й та 90-й процентиль
    low = np.array([np.percentile(h, 10), np.percentile(s, 10), np.percentile(v, 10)], dtype=np.float32)
    high = np.array([np.percentile(h, 90), np.percentile(s, 90), np.percentile(v, 90)], dtype=np.float32)

    # Додаємо подушку
    pad = np.array(pad, dtype=np.float32)
    low -= pad
    high += pad

    # Гарантуємо, що low <= high і все в межах [0,255]
    low = np.clip(low, 0, 255)
    high = np.clip(high, 0, 255)
    low = np.minimum(low, high)  # якщо десь low > high після паду, виправляємо

    return low.astype(np.uint8), high.astype(np.uint8)
