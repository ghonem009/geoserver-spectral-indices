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
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>ndvi_LC08_L1TP_174041_20260214_20260214_02_RT_B4</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp">
              <sld:ColorMapEntry color="#00204d" quantity="-0.32765719999999998" label="-0.33"/>
              <sld:ColorMapEntry color="#31446b" quantity="-0.18191971999999998" label="-0.18"/>
              <sld:ColorMapEntry color="#666970" quantity="-0.036182239999999977" label="-0.04"/>
              <sld:ColorMapEntry color="#969078" quantity="0.10955524000000005" label="0.11"/>
              <sld:ColorMapEntry color="#12e54a" quantity="0.25529272000000003" label="0.26"/>
              <sld:ColorMapEntry color="#088738" quantity="0.4010302" label="0.40"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>

"""

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
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>ndbi_LC08_L1TP_174041_20260214_20260214_02_RT_B6</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp">
              <sld:ColorMapEntry color="#088738" quantity="-0.30517566204071001" label="-0.3052"/>
              <sld:ColorMapEntry color="#fcbea5" quantity="-0.16426972299814199" label="-0.1643"/>
              <sld:ColorMapEntry color="#fb7050" quantity="-0.023363783955574001" label="-0.0234"/>
              <sld:ColorMapEntry color="#d32020" quantity="0.117542155086994" label="0.1175"/>
              <sld:ColorMapEntry color="#67000d" quantity="0.25844809412956199" label="0.2584"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
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
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>ndbi_LC08_L1TP_174041_20260214_20260214_02_RT_B6</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp">
              <sld:ColorMapEntry color="#d7191c" quantity="-0.30517566204071001" label="-0.3052"/>
              <sld:ColorMapEntry color="#fff2b0" quantity="-0.046493891812774579" label="-0.0465"/>
              <sld:ColorMapEntry color="#fff4b2" quantity="-0.042667757136794382" label="-0.0427"/>
              <sld:ColorMapEntry color="#fff7b6" quantity="-0.037354132499498927" label="-0.0374"/>
              <sld:ColorMapEntry color="#e5f4b7" quantity="0.020425104383774817" label="0.0204"/>
              <sld:ColorMapEntry color="#2b83ba" quantity="0.25844786847877699" label="0.2584"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>

"""

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
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>mndwi_LC08_L1TP_174041_20260214_20260214_02_RT_B3</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp">
              <sld:ColorMapEntry color="#f7fbff" quantity="-0.4024469" label="-٠.٤٠٢٤"/>
              <sld:ColorMapEntry color="#deebf7" quantity="-0.29262845100000001" label="-٠.٢٩٢٦"/>
              <sld:ColorMapEntry color="#c6dbef" quantity="-0.182810002" label="-٠.١٨٢٨"/>
              <sld:ColorMapEntry color="#9ecae1" quantity="-0.072991553000000001" label="-٠.٠٧٣٠"/>
              <sld:ColorMapEntry color="#6baed6" quantity="0.036826895999999998" label="٠.٠٣٦٨"/>
              <sld:ColorMapEntry color="#4292c6" quantity="0.14664534500000001" label="٠.١٤٦٦"/>
              <sld:ColorMapEntry color="#2171b5" quantity="0.25646379400000002" label="٠.٢٥٦٥"/>
              <sld:ColorMapEntry color="#08519c" quantity="0.35783467000000002" label="٠.٣٥٧٨"/>
              <sld:ColorMapEntry color="#08306b" quantity="0.44231039999999999" label="٠.٤٤٢٣"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
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