from flask import Flask, render_template
import io
import base64
import air_pollution_core.proceeder as ap
from PIL import Image

app = Flask(__name__)
proceeder = ap.SatelliteImageProceeder()

@app.route("/")
def root():
    return "Server OK"


@app.route("/<region>")
def index(region):
    result_data = None
    image_base64 = None

    if region:
        result = proceeder.process_by_place(region)

        if isinstance(result, dict):
            img_io = io.BytesIO()
            result["image"].save(img_io, "PNG")
            img_io.seek(0)
            image_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")

            result_data = {
                "region": region,
                "trees_area": result["trees"]["area_hectares"],
                "fields_area": result["fields"]["area_hectares"],
                "estimated_trees": result["trees"]["estimated_trees"],
                "forest_coverage": result["forest_coverage_percent"],
                "trees_to_plant": result["trees_to_plant_for_clean_air"],
                "planting_density": result["planting_density_m2"]
            }
        else:
            img_io = io.BytesIO()
            result.save(img_io, "PNG")
            img_io.seek(0)
            image_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")
            result_data = {"region": region}

    return render_template("index.html", result=result_data, image_base64=image_base64)

app.run(debug=True)


