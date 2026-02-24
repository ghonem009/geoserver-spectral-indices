from osgeo import gdal
import numpy as np
import os
from fastapi import UploadFile

class FileManager:
    @staticmethod
    def save_file(upload_file: UploadFile, path: str):
        with open(path, "wb") as f:
            f.write(upload_file.file.read())

    @staticmethod
    def delete_file(file_path: str):
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def create_folder(folder_name: str):
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)


class NDVICreator:

    def __init__(self, red_file, nir_file, output_file, nodata=-9999):
        self.red_file = red_file
        self.nir_file = nir_file
        self.output_file = output_file
        self.nodata = nodata

    def create(self):
        if not os.path.exists(self.red_file) or not os.path.exists(self.nir_file):
            return {"status": "warning", "message": "missing input band"}

        try:
            red_ds = self.open_raster(self.red_file)
            nir_ds = self.open_raster(self.nir_file)

            red = self.read_band(red_ds)
            nir = self.read_band(nir_ds)

            if red is None or nir is None:
                return {"status": "warning", "message": "one of the bands has no data"}

            ndvi_result = self.calculate_ndvi(nir, red)
            self.write_raster(red_ds, ndvi_result)

            return {"status": "success", "output_file": self.output_file}

        except Exception as e:
            return {"status": "error", "message": str(e)}
        

    def open_raster(self, path):
        ds = gdal.Open(path, gdal.GA_ReadOnly)
        if ds is None:
            raise RuntimeError(f"cannot open raster file: {path}")
        return ds

    def read_band(self, ds):
        band = ds.GetRasterBand(1)
        if band is None:
            return None
        arr = band.ReadAsArray().astype("float32")
        ndv = band.GetNoDataValue()
        if ndv is not None:
            arr[arr == ndv] = np.nan
        return arr

    def calculate_ndvi(self, nir, red):
        denom = (nir + red)
        denom[denom == 0] = np.nan
        ndvi = (nir - red) / denom
        ndvi[np.isnan(ndvi)] = self.nodata
        return ndvi

    def write_raster(self, template_ds, data):
        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(
            self.output_file,
            template_ds.RasterXSize,
            template_ds.RasterYSize,
            1,
            gdal.GDT_Float32
        )
        out_ds.SetGeoTransform(template_ds.GetGeoTransform())
        out_ds.SetProjection(template_ds.GetProjection())
        band = out_ds.GetRasterBand(1)
        band.WriteArray(data)
        band.SetNoDataValue(self.nodata)
        band.FlushCache()
        out_ds = None


class NDWICreator(NDVICreator):
    def calculate_ndwi(self, green, nir):
        denom = (green + nir)
        denom[denom == 0] = np.nan
        ndwi = (green - nir) / denom
        ndwi[np.isnan(ndwi)] = self.nodata
        return ndwi

    def create(self):
        try:
            green_ds = self.open_raster(self.red_file)
            nir_ds = self.open_raster(self.nir_file)

            green = self.read_band(green_ds)
            nir = self.read_band(nir_ds)

            if green is None or nir is None:
                return {"status": "warning", "message": "one of the bands has no data"}

            ndwi_result = self.calculate_ndwi(green, nir)
            self.write_raster(green_ds, ndwi_result)

            return {"status": "success", "output_file": self.output_file}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class NDBICreator(NDVICreator):
    def calculate_ndbi(self, swir, nir):
        denom = (swir + nir)
        denom[denom == 0] = np.nan
        ndbi = (swir - nir) / denom
        ndbi[np.isnan(ndbi)] = self.nodata
        return ndbi

    def create(self):
        try:
            swir_ds = self.open_raster(self.red_file)
            nir_ds = self.open_raster(self.nir_file)

            swir = self.read_band(swir_ds)
            nir = self.read_band(nir_ds)

            if swir is None or nir is None:
                return {"status": "warning", "message": "one of the bands has no data"}

            ndbi_result = self.calculate_ndbi(swir, nir)
            self.write_raster(swir_ds, ndbi_result)

            return {"status": "success", "output_file": self.output_file}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class MNDWICreator(NDVICreator):
    def calculate_mndwi(self, green, swir):
        denom = (green + swir)
        denom[denom == 0] = np.nan
        mndwi = (green - swir) / denom
        mndwi[np.isnan(mndwi)] = self.nodata
        return mndwi

    def create(self):
        try:
            green_ds = self.open_raster(self.red_file)
            swir_ds = self.open_raster(self.nir_file)

            green = self.read_band(green_ds)
            swir = self.read_band(swir_ds)

            if green is None or swir is None:
                return {"status": "warning", "message": "one of the bands has no data"}

            mndwi_result = self.calculate_mndwi(green, swir)
            self.write_raster(green_ds, mndwi_result)

            return {"status": "success", "output_file": self.output_file}
        except Exception as e:
            return {"status": "error", "message": str(e)}