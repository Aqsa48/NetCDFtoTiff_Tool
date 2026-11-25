# NetCDF to GeoTIFF

Convert a regular latitude-longitude scientific grid into a north-up GeoTIFF for QGIS and other GIS tools. Use the public browser tool for small NetCDF3 files, or install the Python package for NetCDF4, gzip, and larger datasets.

**[Open the public converter](https://aqsa-netcdf-to-geotiff.aqsa-35.chatgpt.site)** · [Report a bug](https://github.com/Aqsa48/NetCDFtoTiff_Tool/issues) · [Contribute](CONTRIBUTING.md)

## Browser tool

Try the synthetic example or choose a local `.nc` / `.nc.gz` file. Select a variable, coordinate axes, and each time/level index, confirm WGS84 degrees, then download the GeoTIFF. Conversion runs entirely on your device. Files are not uploaded.

The browser supports **NetCDF3 classic and 64-bit offset**, up to **64 MiB decompressed**. Output is a single-band, uncompressed Float64 GeoTIFF with EPSG:4326, PixelIsArea, and NaN nodata. Scale/offset and missing-value metadata are decoded. Unsigned packed variables need the Python tool. An all-missing slice produces an entirely nodata raster.

## Python tool

Python 3.10 or later:

```sh
git clone https://github.com/Aqsa48/NetCDFtoTiff_Tool.git
cd NetCDFtoTiff_Tool
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
python examples/make_sample.py
nc2tiff examples/sample.nc --list
nc2tiff examples/sample.nc temperature.tif --variable temperature --isel time=0
```

The example is generated locally. Expected bounds: west **6.5**, south **44.5**, east **9.5**, north **46.5**. The north row is `[20, NaN, 22]`; the south row is `[10, 11, 12]`.

For the coordinate names used in the original notebook:

```sh
nc2tiff forcing.nc.gz terrain.tif --variable Terrain --lat Latitude --lon Longitude --isel time=0
```

Pass only selectors that exist on your variable. Repeat `--isel` for other non-spatial dimensions. Existing files are protected unless you pass `--overwrite`.

```python
from nc2tiff import convert
result = convert('input.nc', 'rain.tif', 'Rain',
                 lat='Latitude', lon='Longitude', selectors={'time': 0})
print(result)
```

Python output uses lossless DEFLATE compression. Values, CRS, and transform are checked by reopening a temporary GeoTIFF before moving it to the destination. xarray decodes NetCDF scale factors, offsets, and fill values. Nonfinite values become NaN nodata.

## Supported geography

- WGS84 longitude/latitude in degrees, interpreted as **pixel centers**.
- At least two points per axis, regular spacing, and strictly monotonic coordinates.
- 1D axes, or 2D rectilinear grids where latitude is constant along each row and longitude along each column.
- Either axis direction; data are reordered from the actual coordinates.

Curvilinear, projected, rotated, irregular, 0–360 longitude, and dateline-crossing grids require preprocessing or regridding. This tool does not infer a datum or reproject. Confirm WGS84 before use. Coordinate bounds variables are not used. Time values are not rewritten or guessed from filenames.

`main.ipynb` preserves the original site-specific workflow. The package and browser app are the reusable entry points.

## Development

```sh
python -m pip install ".[test]"
python -m pytest -q
python examples/make_sample.py
node web/test-core.mjs
python -m http.server 8000 --directory web
```

If regenerating the browser fixture, copy `examples/sample.nc` to `web/sample.nc`. The browser has no build step or remote script dependencies. See [third-party notices](web/THIRD_PARTY_NOTICES.md) for the vendored parser. Its GeoTIFF writer is checked with Rasterio independently of the browser parser.

## Other main projects

[Data Science lessons](https://github.com/Aqsa48/Data-Science) · [Variant feature datasets](https://github.com/Aqsa48/Federated-Learning-for-Non-IID-Data-SARS-CoV-2-Variant-Classification-Dataset) · [Learn by Doing](https://github.com/Aqsa48/earning_by_learning_resources)
