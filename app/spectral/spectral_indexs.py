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

    def get_sld(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>NDVI</Name>
    <UserStyle>
      <Title>NDVI Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ChannelSelection>
              <GrayChannel><SourceChannelName>1</SourceChannelName></GrayChannel>
            </ChannelSelection>
            <ColorMap type="ramp">
              <ColorMapEntry color="#d73027" quantity="-1.0"  label="-1.0" opacity="1"/>
              <ColorMapEntry color="#f46d43" quantity="-0.5"  label="-0.5" opacity="1"/>
              <ColorMapEntry color="#fdae61" quantity="-0.2"  label="-0.2" opacity="1"/>
              <ColorMapEntry color="#fee08b" quantity="0.0"   label="0.0"  opacity="1"/>
              <ColorMapEntry color="#d9ef8b" quantity="0.2"   label="0.2"  opacity="1"/>
              <ColorMapEntry color="#a6d96a" quantity="0.4"   label="0.4"  opacity="1"/>
              <ColorMapEntry color="#66bd63" quantity="0.6"   label="0.6"  opacity="1"/>
              <ColorMapEntry color="#1a9850" quantity="1.0"   label="1.0"  opacity="1"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

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

    def get_sld(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>NDWI</Name>
    <UserStyle>
      <Title>NDWI Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ChannelSelection>
              <GrayChannel><SourceChannelName>1</SourceChannelName></GrayChannel>
            </ChannelSelection>
            <ColorMap type="ramp">
              <ColorMapEntry color="#8c510a" quantity="-1.0"  label="-1.0 (dry)"   opacity="1"/>
              <ColorMapEntry color="#d8b365" quantity="-0.3"  label="-0.3"         opacity="1"/>
              <ColorMapEntry color="#f6e8c3" quantity="0.0"   label="0.0"          opacity="1"/>
              <ColorMapEntry color="#c7eae5" quantity="0.1"   label="0.1"          opacity="1"/>
              <ColorMapEntry color="#5ab4ac" quantity="0.3"   label="0.3"          opacity="1"/>
              <ColorMapEntry color="#01665e" quantity="1.0"   label="1.0 (water)"  opacity="1"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

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

    def get_sld(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>NDBI</Name>
    <UserStyle>
      <Title>NDBI Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ChannelSelection>
              <GrayChannel><SourceChannelName>1</SourceChannelName></GrayChannel>
            </ChannelSelection>
            <ColorMap type="ramp">
              <ColorMapEntry color="#1a9641" quantity="-1.0"  label="-1.0 (veg/water)" opacity="1"/>
              <ColorMapEntry color="#a6d96a" quantity="-0.3"  label="-0.3"             opacity="1"/>
              <ColorMapEntry color="#ffffbf" quantity="0.0"   label="0.0"              opacity="1"/>
              <ColorMapEntry color="#fdae61" quantity="0.3"   label="0.3"              opacity="1"/>
              <ColorMapEntry color="#d7191c" quantity="1.0"   label="1.0 (built-up)"  opacity="1"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

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

    def get_sld(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>MNDWI</Name>
    <UserStyle>
      <Title>MNDWI Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ChannelSelection>
              <GrayChannel><SourceChannelName>1</SourceChannelName></GrayChannel>
            </ChannelSelection>
            <ColorMap type="ramp">
              <ColorMapEntry color="#7f3b08" quantity="-1.0"  label="-1.0 (land/bare)"  opacity="1"/>
              <ColorMapEntry color="#e08214" quantity="-0.3"  label="-0.3"              opacity="1"/>
              <ColorMapEntry color="#fdb863" quantity="0.0"   label="0.0"               opacity="1"/>
              <ColorMapEntry color="#b2e2e2" quantity="0.1"   label="0.1"               opacity="1"/>
              <ColorMapEntry color="#238b45" quantity="0.3"   label="0.3"               opacity="1"/>
              <ColorMapEntry color="#003c30" quantity="1.0"   label="1.0 (open water)"  opacity="1"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""

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