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
result = proceeder.process_by_place("Lytovezh")
result.show()

