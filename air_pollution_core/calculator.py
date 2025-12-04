import numpy as np

class AreaCalculator:

    @staticmethod
    def estimate_area_and_trees(mask: np.ndarray, pixel_to_m2: float, trees_per_m2: float):
        non_zero_pixels = int(np.count_nonzero(mask))
        area_m2 = non_zero_pixels * pixel_to_m2
        area_ha = area_m2 / 10_000
        trees_est = area_m2 * trees_per_m2
        return non_zero_pixels, area_m2, area_ha, trees_est

    @staticmethod
    def calculate_forest_data(mask_trees: np.ndarray, mask_fields: np.ndarray, pixel_to_m2: float,
                              trees_per_m2: float, pollution: dict):
        trees_px, trees_m2, trees_ha, existing_trees = AreaCalculator.estimate_area_and_trees(
            mask_trees, pixel_to_m2, trees_per_m2
        )
        fields_px, fields_m2, fields_ha, _ = AreaCalculator.estimate_area_and_trees(
            mask_fields, pixel_to_m2, trees_per_m2
        )

        height, width = mask_trees.shape
        total_area_m2 = height * width * pixel_to_m2
        forest_percent = trees_m2 / total_area_m2 if total_area_m2 > 0 else 0

        current_aqi = pollution.get("aqi", 0)
        target_aqi = 50  
        trees_to_plant = 0
        planting_density_m2 = 0.0

        if current_aqi > target_aqi and fields_m2 > 0:
            trees_to_plant = max(0, int(existing_trees * (current_aqi / target_aqi - 1)))
            planting_density_m2 = trees_to_plant / fields_m2

        return {
            "trees": {
                "pixels": trees_px,
                "area_m2": round(trees_m2, 2),
                "area_hectares": round(trees_ha, 4),
                "estimated_trees": int(existing_trees)
            },
            "fields": {
                "pixels": fields_px,
                "area_m2": round(fields_m2, 2),
                "area_hectares": round(fields_ha, 4)
            },
            "forest_coverage_percent": round(forest_percent * 100, 2),
            "trees_to_plant_for_clean_air": trees_to_plant,
            "planting_density_m2": round(trees_per_m2, 4),
            "pollution": {
                "current_aqi": current_aqi,
                "category": pollution.get("category", ""),
                "target_aqi": target_aqi,
                "trees_to_plant_for_clean_air": trees_to_plant,
                "planting_density_m2": round(planting_density_m2, 4)
            }
        }
