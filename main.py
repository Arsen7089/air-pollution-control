import lookup
import air_pollution_core as ap
my_api = lookup.FreeAPIManager()
proceeder = ap.SatelliteImageProceeder(api_manager=my_api)
result = proceeder.process_by_place("Lytovezh")
result.show()
