import lookup
import air_pollution_core as ap
import file_storage as fs
from PIL import Image

my_file_storage = fs.LocalFileStorage()
my_api = lookup.FreeAPIManager(my_file_storage)

forest_img = my_file_storage.load("forest_full")
field_img = my_file_storage.load("field_full")

proceeder = ap.SatelliteImageProceeder(
    api_manager=my_api,
    forest_img=forest_img,
    field_img=field_img,
)

result = proceeder.process_by_place("Lviv")

if isinstance(result, dict):
    result["image"].show()

    print("Результати аналізу регіону Lviv")
    print(f"Площа лісу (гектари): {result['trees']['area_hectares']}")
    print(f"Площа полів (гектари): {result['fields']['area_hectares']}")
    print(f"Орієнтовна кількість дерев: {result['trees']['estimated_trees']}")
    print(f"Покриття лісами: {result['forest_coverage_percent']} %")
    print(f"Необхідно досадити дерев: {result['trees_to_plant_for_clean_air']}")
    print(f"Маштаб: {my_api.compute_pixel_scale(49)}")
    print(f"Густина посіву: {result['planting_density_m2']}")
else:
    result.show()
