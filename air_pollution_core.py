from PIL import Image
import numpy as np
import cv2
from lookup import AbstractAPIManager
import photo_formatter


class SatelliteImageProceeder:
    def __init__(
        self,
        api_manager: AbstractAPIManager,
        forest_img: Image.Image,
        field_img: Image.Image
    ):
        """
        Клас працює на основі переданих зображень для калібрування.
        HSV-діапазони зберігаються лише в пам'яті.
        Працює лише з trees і fields.
        """
        self.api = api_manager

        if forest_img is None or field_img is None:
            raise RuntimeError("Calibration images missing (forest/field).")

        # Калібруємо HSV-діапазони
        self.hsv_ranges = {
            "trees": photo_formatter.analyze_hsv_range(forest_img),
            "fields": photo_formatter.analyze_hsv_range(field_img),
        }

        print("✅ Calibration completed. HSV ranges:")
        for name, (low, high) in self.hsv_ranges.items():
            print(f"  {name}: low={low.tolist()}, high={high.tolist()}")

    def process_satellite_image(self, image_pil: Image.Image, cols: int = 2, rows: int = 2, debug: bool = False) -> Image.Image:
        """
        Обробка супутникового зображення на основі HSV-діапазонів в пам'яті.
        Працює лише з trees і fields.
        """
        img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        height, width = img_cv.shape[:2]
        tile_w, tile_h = width // cols, height // rows

        processed_rows = []
        low_t, high_t = self.hsv_ranges["trees"]
        low_f, high_f = self.hsv_ranges["fields"]

        for y in range(rows):
            row_tiles = []
            for x in range(cols):
                tile = img_cv[y*tile_h:(y+1)*tile_h, x*tile_w:(x+1)*tile_w]

                shifted = cv2.pyrMeanShiftFiltering(tile, 5, 20)
                hsv = cv2.cvtColor(shifted, cv2.COLOR_BGR2HSV)

                mask_trees = cv2.inRange(hsv, low_t, high_t)
                mask_fields = cv2.inRange(hsv, low_f, high_f)
                
                mask_fields = cv2.bitwise_and(mask_fields, cv2.bitwise_not(mask_trees))

                if debug:
                    print(f"Tile ({x},{y}): trees={np.count_nonzero(mask_trees)}, "
                          f"fields={np.count_nonzero(mask_fields)}")

                overlay = tile.copy()
                overlay[mask_fields > 0] = (0, 0, 255)
                overlay[mask_trees > 0] = (255, 0, 0)

                blended = cv2.addWeighted(tile, 0.8, overlay, 0.2, 0)
                row_tiles.append(blended)

            processed_rows.append(np.hstack(row_tiles))

        combined = np.vstack(processed_rows)
        return Image.fromarray(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))

    def process_by_place(self, place_name: str, cols=2, rows=2, debug=False) -> Image.Image:
        """
        Отримати фото за місцем через API та обробити.
        """
        photo = self.api.get_photo_by_place(place_name)
        if not photo:
            raise ValueError(f"❌ No image available for '{place_name}'")
        return self.process_satellite_image(photo, cols, rows, debug)
