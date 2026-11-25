"""Verify JS-generated GeoTIFF using an independent GDAL-backed reader."""
from pathlib import Path
import numpy as np
import rasterio

with rasterio.open(Path(__file__).with_name("test-output.tif")) as image:
    np.testing.assert_array_equal(image.read(1), [[20., np.nan, 22.], [10., 11., 12.]])
    assert image.crs.to_epsg() == 4326
    assert tuple(image.bounds) == (6.5, 44.5, 9.5, 46.5)
    assert image.dtypes == ("float64",)
    assert np.isnan(image.nodata)
print("Browser GeoTIFF verified with Rasterio: values, bounds, CRS, dtype, nodata.")
