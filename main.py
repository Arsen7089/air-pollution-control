import lookup
import air_pollution_core as ap
import photo_storage as ps
my_api = lookup.FreeAPIManager()
my_photo_storage = ps.LocalPhotoStorage()
proceeder = ap.SatelliteImageProceeder(api_manager=my_api, photo_storage=my_photo_storage)
result = proceeder.process_by_place("Novovolynsk")
result.show()
