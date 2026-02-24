from fastapi import FastAPI, UploadFile, File
import os
import requests
from app.spectral.spectral_indexs import NDVICreator, NDWICreator, NDBICreator, MNDWICreator, FileManager

app = FastAPI()

INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"

FileManager.create_folder(INPUT_FOLDER)
FileManager.create_folder(OUTPUT_FOLDER)

geo_url = "http://localhost:8080/geoserver"
geo_user = "admin"
geo_pass = "geoserver"
workspace = "spectral_indexes"

def upload_layer_to_geoserver(file_path, layer_name):
    url = f"{geo_url}/rest/workspaces/{workspace}/coveragestores/{layer_name}/file.geotiff"
    with open(file_path, "rb") as f:
        response = requests.put(
            url,
            auth=(geo_user, geo_pass),
            headers={"Content-type": "image/tiff"},
            data=f
        )
    if response.status_code in [200, 201]:
        return {"status": "success", "message": f"Layer '{layer_name}' uploaded"}
    else:
        return {"status": "error", "message": response.text}

@app.post("/ndvi")
def create_ndvi(red_file: UploadFile = File(...), nir_file: UploadFile = File(...)):
    red_path = os.path.join(INPUT_FOLDER, red_file.filename)
    nir_path = os.path.join(INPUT_FOLDER, nir_file.filename)
    output_file = os.path.join(OUTPUT_FOLDER, f"ndvi_{red_file.filename}")

    try:
        FileManager.save_file(red_file, red_path)
        FileManager.save_file(nir_file, nir_path)

        result = NDVICreator(red_path, nir_path, output_file).create()

        if result["status"] == "success":
            layer_name = f"ndvi_{os.path.splitext(red_file.filename)[0]}"
            geo_result = upload_layer_to_geoserver(output_file, layer_name)
            result["geoserver"] = geo_result

        return result

    finally:
        FileManager.delete_file(red_path)
        FileManager.delete_file(nir_path)

@app.post("/ndwi")
def create_ndwi(green_file: UploadFile = File(...), nir_file: UploadFile = File(...)):
    green_path = os.path.join(INPUT_FOLDER, green_file.filename)
    nir_path = os.path.join(INPUT_FOLDER, nir_file.filename)
    output_file = os.path.join(OUTPUT_FOLDER, f"ndwi_{green_file.filename}")

    try:
        FileManager.save_file(green_file, green_path)
        FileManager.save_file(nir_file, nir_path)

        result = NDWICreator(green_path, nir_path, output_file).create()

        if result["status"] == "success":
            layer_name = f"ndwi_{os.path.splitext(green_file.filename)[0]}"
            geo_result = upload_layer_to_geoserver(output_file, layer_name)
            result["geoserver"] = geo_result

        return result

    finally:
        FileManager.delete_file(green_path)
        FileManager.delete_file(nir_path)

@app.post("/ndbi")
def create_ndbi(swir_file: UploadFile = File(...), nir_file: UploadFile = File(...)):
    swir_path = os.path.join(INPUT_FOLDER, swir_file.filename)
    nir_path = os.path.join(INPUT_FOLDER, nir_file.filename)
    output_file = os.path.join(OUTPUT_FOLDER, f"ndbi_{swir_file.filename}")

    try:
        FileManager.save_file(swir_file, swir_path)
        FileManager.save_file(nir_file, nir_path)

        result = NDBICreator(swir_path, nir_path, output_file).create()

        if result["status"] == "success":
            layer_name = f"ndbi_{os.path.splitext(swir_file.filename)[0]}"
            geo_result = upload_layer_to_geoserver(output_file, layer_name)
            result["geoserver"] = geo_result

        return result

    finally:
        FileManager.delete_file(swir_path)
        FileManager.delete_file(nir_path)

@app.post("/mndwi")
def create_mndwi(green_file: UploadFile = File(...), swir_file: UploadFile = File(...)):
    green_path = os.path.join(INPUT_FOLDER, green_file.filename)
    swir_path = os.path.join(INPUT_FOLDER, swir_file.filename)
    output_file = os.path.join(OUTPUT_FOLDER, f"mndwi_{green_file.filename}")

    try:
        FileManager.save_file(green_file, green_path)
        FileManager.save_file(swir_file, swir_path)

        result = MNDWICreator(green_path, swir_path, output_file).create()

        if result["status"] == "success":
            layer_name = f"mndwi_{os.path.splitext(green_file.filename)[0]}"
            geo_result = upload_layer_to_geoserver(output_file, layer_name)
            result["geoserver"] = geo_result

        return result

    finally:
        FileManager.delete_file(green_path)
        FileManager.delete_file(swir_path)