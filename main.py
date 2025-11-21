import lookup
import air_pollution_core as ap
import file_storage as fs
my_api = lookup.FreeAPIManager()
my_file_storage = fs.LocalFileStorage()
proceeder = ap.SatelliteImageProceeder(api_manager=my_api, file_storage=my_file_storage)
result = proceeder.process_by_place("Novovolynsk")
result.show()
