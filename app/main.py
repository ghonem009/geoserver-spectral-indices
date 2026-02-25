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


def upload_sld_to_geoserver(style_name, sld_body):
    url = f"{geo_url}/rest/styles"
    headers = {"Content-Type": "application/vnd.ogc.sld+xml"}
    auth = (geo_user, geo_pass)

    response = requests.post(
        url,
        auth=auth,
        headers=headers,
        params={"name": style_name},
        data=sld_body.encode("utf-8"),
    )

    if response.status_code in [200, 201]:
        return {"status": "success", "message": f"Style '{style_name}' uploaded"}
    else:
        return {"status": "error", "message": f"Upload failed ({response.status_code}): {response.text}"}


def assign_style_to_layer(layer_name, style_name):
    url = f"{geo_url}/rest/layers/{workspace}:{layer_name}"
    payload = {"layer": {"defaultStyle": {"name": style_name, "workspace": workspace}}}
    requests.put(url, auth=(geo_user, geo_pass), json=payload)
    return {"status": "done", "layer": layer_name, "style": style_name}


def publish_with_style(file_path, layer_name, sld_body):
    style_name = f"{layer_name}_style"

    upload_layer_to_geoserver(file_path, layer_name)  
    upload_sld_to_geoserver(style_name, sld_body)      
    assign_style_to_layer(layer_name, style_name)     

    return {"layer": layer_name, "style": style_name, "status": "published"}


@app.post("/ndvi")
def create_ndvi(red_file: UploadFile = File(...), nir_file: UploadFile = File(...)):
    red_path = os.path.join(INPUT_FOLDER, red_file.filename)
    nir_path = os.path.join(INPUT_FOLDER, nir_file.filename)
    output_file = os.path.join(OUTPUT_FOLDER, f"ndvi_{red_file.filename}")

    try:
        FileManager.save_file(red_file, red_path)
        FileManager.save_file(nir_file, nir_path)

        creator = NDVICreator(red_path, nir_path, output_file)
        result = creator.create()

        if result["status"] == "success":
            layer_name = f"ndvi_{os.path.splitext(red_file.filename)[0]}"
            result["geoserver"] = publish_with_style(output_file, layer_name, creator.get_sld())

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

        creator = NDWICreator(green_path, nir_path, output_file)
        result = creator.create()

        if result["status"] == "success":
            layer_name = f"ndwi_{os.path.splitext(green_file.filename)[0]}"
            result["geoserver"] = publish_with_style(output_file, layer_name, creator.get_sld())

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

        creator = NDBICreator(swir_path, nir_path, output_file)
        result = creator.create()

        if result["status"] == "success":
            layer_name = f"ndbi_{os.path.splitext(swir_file.filename)[0]}"
            result["geoserver"] = publish_with_style(output_file, layer_name, creator.get_sld())

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

        creator = MNDWICreator(green_path, swir_path, output_file)
        result = creator.create()

        if result["status"] == "success":
            layer_name = f"mndwi_{os.path.splitext(green_file.filename)[0]}"
            result["geoserver"] = publish_with_style(output_file, layer_name, creator.get_sld())

        return result

    finally:
        FileManager.delete_file(green_path)
        FileManager.delete_file(swir_path)