# NetCDF to GeoTIFF

[![Launch the converter](https://img.shields.io/badge/Launch-public_converter-006B77?style=for-the-badge)](https://aqsabrohi.me/NetCDFtoTiff_Tool/)
[![GitHub Pages](https://github.com/Aqsa48/NetCDFtoTiff_Tool/actions/workflows/pages.yml/badge.svg)](https://github.com/Aqsa48/NetCDFtoTiff_Tool/actions/workflows/pages.yml)
[![Project checks](https://github.com/Aqsa48/NetCDFtoTiff_Tool/actions/workflows/checks.yml/badge.svg)](https://github.com/Aqsa48/NetCDFtoTiff_Tool/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**[Live application](https://aqsabrohi.me/NetCDFtoTiff_Tool/)** · **[GitHub repository](https://github.com/Aqsa48/NetCDFtoTiff_Tool)**

[Browser guide](#browser-tool) · [Python setup](#python-tool) · [Supported grids](#supported-geography) · [Troubleshooting](#troubleshooting) · [Contribute](#development)

## Choose your starting point

| I want to… | Start here |
| --- | --- |
| Try the tool without installing anything | [Open the converter](https://aqsabrohi.me/NetCDFtoTiff_Tool/), then click **Try a synthetic example** |
| Convert a small NetCDF3 file | [Browser workflow](#browser-tool) |
| Convert NetCDF4/HDF5 or a larger file | [Install the Python tool](#python-tool) |
| Inspect a known input first | [Download the synthetic NetCDF fixture](https://raw.githubusercontent.com/Aqsa48/NetCDFtoTiff_Tool/main/web/sample.nc) |
| Use the converter in a script | [Python API example](#use-from-python) |
| Improve the tool | [Contributor guide](CONTRIBUTING.md) |

GitHub provides the expandable guides below. The file picker, preview, and conversion run in the linked live application.


Convert a regular latitude-longitude scientific grid into a north-up GeoTIFF for QGIS and other GIS tools. Use the public browser tool for small NetCDF3 files, or install the Python package for NetCDF4, gzip, and larger datasets.

**[Open the public converter](https://aqsabrohi.me/NetCDFtoTiff_Tool/)** · [Report a bug](https://github.com/Aqsa48/NetCDFtoTiff_Tool/issues) · [Contribute](CONTRIBUTING.md)

## Browser tool

<details open>
<summary><strong>Try the public converter in five steps</strong></summary>

1. [Launch the application](https://aqsabrohi.me/NetCDFtoTiff_Tool/).
2. Click **Try a synthetic example**, or choose a local `.nc` / `.nc.gz` file.
3. Select the variable, latitude and longitude coordinates, and each extra dimension index.
4. Confirm WGS84 degrees, then click **Create GeoTIFF**.
5. Inspect the preview and bounds, then click **Download GeoTIFF**.

For the synthetic example, time index **0** gives five valid cells and one missing cell. Change the index to **1** and convert again for a slice with six valid cells.

</details>

Try the synthetic example or choose a local `.nc` / `.nc.gz` file. Select a variable, coordinate axes, and each time/level index, confirm WGS84 degrees, then download the GeoTIFF. Conversion runs entirely on your device. Files are not uploaded.

The browser supports **NetCDF3 classic and 64-bit offset**, up to **64 MiB decompressed**. Output is a single-band, uncompressed Float64 GeoTIFF with EPSG:4326, PixelIsArea, and NaN nodata. Scale/offset and missing-value metadata are decoded. Unsigned packed variables need the Python tool. An all-missing slice produces an entirely nodata raster.

## Python tool

Python 3.10 or later. Expand the setup guide for your operating system.

<details>
<summary><strong>Windows PowerShell setup</strong></summary>

```powershell
git clone https://github.com/Aqsa48/NetCDFtoTiff_Tool.git
cd NetCDFtoTiff_Tool
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe examples/make_sample.py
.\.venv\Scripts\nc2tiff.exe examples/sample.nc --list
.\.venv\Scripts\nc2tiff.exe examples/sample.nc temperature.tif --variable temperature --isel time=0
```

These commands call the virtual environment directly; activation is optional.

</details>

<details>
<summary><strong>Linux / macOS setup</strong></summary>

```sh
git clone https://github.com/Aqsa48/NetCDFtoTiff_Tool.git
cd NetCDFtoTiff_Tool
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python examples/make_sample.py
.venv/bin/nc2tiff examples/sample.nc --list
.venv/bin/nc2tiff examples/sample.nc temperature.tif --variable temperature --isel time=0
```

</details>

<details>
<summary><strong>Setup with an activated virtual environment</strong></summary>


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

</details>

<details>
<summary><strong>What should the example output look like?</strong></summary>

The example is generated locally. Expected bounds: west **6.5**, south **44.5**, east **9.5**, north **46.5**. The north row is `[20, NaN, 22]`; the south row is `[10, 11, 12]`.

| Output property | Expected value |
| --- | --- |
| Raster size | 3 columns × 2 rows |
| Coordinate system | EPSG:4326 |
| Valid / missing cells at time 0 | 5 / 1 |
| Cell size | 1° × 1° |
| Nodata | NaN |

</details>

<details>
<summary><strong>Custom coordinate names and time/level selection</strong></summary>

For the coordinate names used in the original notebook:

```sh
nc2tiff forcing.nc.gz terrain.tif --variable Terrain --lat Latitude --lon Longitude --isel time=0
```

Pass only selectors that exist on your variable. Repeat `--isel` for other non-spatial dimensions. Existing files are protected unless you pass `--overwrite`.

</details>

### Use from Python

<details>
<summary><strong>Expand the reusable Python API example</strong></summary>

```python
from nc2tiff import convert
result = convert('input.nc', 'rain.tif', 'Rain',
                 lat='Latitude', lon='Longitude', selectors={'time': 0})
print(result)
```

Python output uses lossless DEFLATE compression. Values, CRS, and transform are checked by reopening a temporary GeoTIFF before moving it to the destination. xarray decodes NetCDF scale factors, offsets, and fill values. Nonfinite values become NaN nodata.

</details>

## Supported geography

- WGS84 longitude/latitude in degrees, interpreted as **pixel centers**.
- At least two points per axis, regular spacing, and strictly monotonic coordinates.
- 1D axes, or 2D rectilinear grids where latitude is constant along each row and longitude along each column.
- Either axis direction; data are reordered from the actual coordinates.

Curvilinear, projected, rotated, irregular, 0–360 longitude, and dateline-crossing grids require preprocessing or regridding. This tool does not infer a datum or reproject. Confirm WGS84 before use. Coordinate bounds variables are not used. Time values are not rewritten or guessed from filenames.

`main.ipynb` preserves the original site-specific workflow. The package and browser app are the reusable entry points.

## Troubleshooting

<details>
<summary><strong>My file is NetCDF4/HDF5 or exceeds 64 MiB</strong></summary>

Use the [Python tool](#python-tool). The browser handles NetCDF3 classic and 64-bit offset formats only. Its 64 MiB limit applies after gzip decompression.

</details>

<details>
<summary><strong>The tool asks for a dimension index</strong></summary>

Choose an index for every non-spatial dimension. In the browser, fill each time/level field. With Python, inspect dimensions first:

```sh
nc2tiff input.nc --list
nc2tiff input.nc output.tif --variable temperature --isel time=0 --isel level=0
```

Use only dimensions reported for your variable. Indices start at zero.

</details>

<details>
<summary><strong>My coordinate variables have different names</strong></summary>

Select those variables in the browser, or pass their exact names:

```sh
nc2tiff input.nc output.tif --variable Terrain --lat Latitude --lon Longitude
```

Add selectors if the chosen variable has time or level dimensions. Coordinates must satisfy the [supported geography](#supported-geography).

</details>

<details>
<summary><strong>My grid is irregular, curvilinear, projected, or uses 0–360 longitude</strong></summary>

Regrid, reproject, or normalize coordinates before conversion, then check the geography. Renaming projected coordinates to latitude/longitude does not change their coordinate system.

</details>

<details>
<summary><strong>The output file already exists</strong></summary>

Choose a new path, or intentionally replace it with `--overwrite`:

```sh
nc2tiff input.nc output.tif --variable rain --overwrite
```

</details>

<details>
<summary><strong>I found a different problem</strong></summary>

[Open a bug report](https://github.com/Aqsa48/NetCDFtoTiff_Tool/issues/new?template=bug_report.yml). Include your environment, steps, expected behavior, and a small public or synthetic example. Remove credentials and restricted research data.

</details>

## GitHub Pages deployment

The [public converter](https://aqsabrohi.me/NetCDFtoTiff_Tool/) is hosted on GitHub Pages and deployed by [GitHub Actions](https://github.com/Aqsa48/NetCDFtoTiff_Tool/actions/workflows/pages.yml). Changes to the app on `main` publish automatically after the conversion checks pass. See [deployment instructions](DEPLOYMENT.md) for setup, manual publishing, and troubleshooting.

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
