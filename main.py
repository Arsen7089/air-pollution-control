import air_pollution_core.proceeder as ap

proceeder = ap.SatelliteImageProceeder()
region = "Lviv"
result = proceeder.process_by_place(region)
if isinstance(result, dict):
    result["image"].show()

    print(f"Результати аналізу регіону {region}")
    print(f"Площа лісу (гектари): {result['trees']['area_hectares']}")
    print(f"Площа полів (гектари): {result['fields']['area_hectares']}")
    print(f"Орієнтовна кількість дерев: {result['trees']['estimated_trees']}")
    print(f"Покриття лісами: {result['forest_coverage_percent']} %")
    print(f"Необхідно досадити дерев: {result['trees_to_plant_for_clean_air']}")
    print(f"Густина посіву: {result['planting_density_m2']}")
else:
    result.show()
