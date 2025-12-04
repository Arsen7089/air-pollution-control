from flask import Flask, render_template, request, redirect, url_for, Response
import io
import base64
import air_pollution_core.proceeder as ap
from PIL import Image
import settings.env as settings
from functools import wraps

app = Flask("server")
proceeder = ap.SatelliteImageProceeder(settings.OWM_API, settings.MONGO_IP, settings.MONGO_PORT, settings.MONGO_USER, settings.MONGO_PASS)
storage = proceeder.get_storage()

def check_auth(username, password):
    return username == settings.ADMIN_USER and password == settings.ADMIN_PASS

def authenticate_error():
    return Response(
        'Authentication required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate_error()
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        region = request.form.get("region")
        if region:
            return redirect(url_for("index", region=region))
    return render_template("index.html", result=None, image_base64=None)

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

            pollution = result.get("pollution", {})

            result_data = {
                "region": region,
                "trees_area": result["trees"]["area_hectares"],
                "fields_area": result["fields"]["area_hectares"],
                "estimated_trees": result["trees"]["estimated_trees"],
                "forest_coverage": result["forest_coverage_percent"],
                "trees_to_plant": pollution.get("trees_to_plant_for_clean_air", result.get("trees_to_plant_for_clean_air", 0)),
                "planting_density": result.get("planting_density_m2", 0.0),
                "current_aqi": pollution.get("current_aqi", 0),
                "target_aqi": pollution.get("target_aqi", 50),
                "aqi_category": pollution.get("category", ""),
                "planting_density_for_clean_air": pollution.get("planting_density_m2", 0.0)
            }
        else:
            img_io = io.BytesIO()
            result.save(img_io, "PNG")
            img_io.seek(0)
            image_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")
            result_data = {"region": region}

    return render_template("index.html", result=result_data, image_base64=image_base64)

@app.route("/admin", methods=["GET", "POST"])
@requires_auth
def admin_panel():
    message = None

    if request.method == "POST":
        collection = request.form.get("collection")
        document = request.form.get("document")
        field = request.form.get("field")

        if collection and document:
            file_id = f"{collection}/{document}/{field}" if field else f"{collection}/{document}/*"
            ok = storage.delete(file_id)
            message = f"Deleted: {file_id}" if ok else f"Error deleting {file_id}"
        else:
            message = "Collection and Document are required!"

    db_dump = storage.get_data_dump()
    return render_template("admin.html", collections=db_dump, message=message)
    
app.run(debug=True, host=settings.WEB_IP, port=settings.WEB_PORT)
