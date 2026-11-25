"""Reject unsupported grids instead of silently assigning incorrect geography."""
from contextlib import contextmanager
import gzip
from pathlib import Path
import shutil
import tempfile

import numpy as np
import rasterio
from rasterio.transform import from_origin
import xarray as xr


@contextmanager
def open_dataset(path):
    path = Path(path)
    if path.suffix.lower() == ".gz":
        with tempfile.TemporaryDirectory() as folder:
            unpacked = Path(folder) / "input.nc"
            with gzip.open(path, "rb") as source, unpacked.open("wb") as target:
                shutil.copyfileobj(source, target)
            with xr.open_dataset(unpacked, decode_times=False) as ds:
                yield ds
    else:
        with xr.open_dataset(path, decode_times=False) as ds:
            yield ds


def _axis(values, name, limit):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        raise ValueError(f"{name} must contain at least two finite coordinate centers")
    delta = np.diff(values)
    if not (np.all(delta > 0) or np.all(delta < 0)):
        raise ValueError(f"{name} must be strictly monotonic; dateline wrapping is unsupported")
    if not np.allclose(delta, delta[0], rtol=1e-5, atol=1e-8):
        raise ValueError(f"{name} must be regularly spaced")
    if np.any(np.abs(values) > limit):
        raise ValueError(f"{name} must use geographic degrees within ±{limit}")
    return values


def prepare_grid(ds, variable, *, lat="lat", lon="lon", selectors=None):
    if variable not in ds.data_vars:
        raise ValueError(f"Unknown data variable: {variable}")
    if lat not in ds or lon not in ds:
        raise ValueError("Latitude/longitude coordinates not found; pass --lat and --lon")
    data = ds[variable]
    selectors = selectors or {}
    for dim, index in selectors.items():
        if dim not in data.dims or index < 0 or index >= data.sizes[dim]:
            raise ValueError(f"Invalid selector {dim}={index}")
    # Never select the first time/level silently.
    data = data.isel(selectors)
    latitude, longitude = ds[lat], ds[lon]
    if latitude.ndim == longitude.ndim == 1:
        ydim, xdim = latitude.dims[0], longitude.dims[0]
        y, x = latitude.values, longitude.values
    elif latitude.ndim == longitude.ndim == 2 and latitude.dims == longitude.dims:
        ydim, xdim = latitude.dims
        y, x = latitude.values[:, 0], longitude.values[0, :]
        if not (np.allclose(latitude, y[:, None], rtol=0, atol=1e-7) and
                np.allclose(longitude, x[None, :], rtol=0, atol=1e-7)):
            raise ValueError("Curvilinear coordinates require regridding before conversion")
    else:
        raise ValueError("Coordinates must be 1D axes or matching rectilinear 2D grids")
    if ydim == xdim or set(data.dims) != {ydim, xdim} or data.ndim != 2:
        raise ValueError("Select every non-spatial dimension with --isel dimension=index")
    if ydim in selectors or xdim in selectors:
        raise ValueError("Spatial dimensions cannot be selected")
    x, y = _axis(x, "Longitude", 180), _axis(y, "Latitude", 90)
    if data.sizes[ydim] != len(y) or data.sizes[xdim] != len(x):
        raise ValueError("Coordinate and data shapes differ")
    # Coordinates are explicitly interpreted as WGS84 degrees by this tool.
    if data.attrs.get("grid_mapping"):
        mapping = ds.get(data.attrs["grid_mapping"])
        if mapping is not None and mapping.attrs.get("grid_mapping_name") not in (None, "latitude_longitude"):
            raise ValueError("Projected grids require reprojection before conversion")
    for coordinate in (latitude, longitude):
        units = str(coordinate.attrs.get("units", "")).lower()
        if units and units not in {"degrees_north", "degree_north", "degrees_east", "degree_east", "degrees", "degree"}:
            raise ValueError("Coordinates must use degrees, not projected units")
    if not np.issubdtype(data.dtype, np.number) or np.issubdtype(data.dtype, np.complexfloating):
        raise ValueError("Only real numeric data variables are supported")
    values = np.asarray(data.transpose(ydim, xdim).values, dtype=np.float64)
    if x[0] > x[-1]:
        values = values[:, ::-1]
    if y[0] < y[-1]:
        values = values[::-1, :]
    transform = from_origin(float(x.min() - abs(x[1]-x[0])/2),
                            float(y.max() + abs(y[1]-y[0])/2),
                            float(abs(x[1]-x[0])), float(abs(y[1]-y[0])))
    return values, transform


def convert(source, destination, variable, *, lat="lat", lon="lon", selectors=None, overwrite=False):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Input and output paths must differ")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"Output exists: {destination}; pass --overwrite to replace it")
    with open_dataset(source) as ds:
        values, transform = prepare_grid(ds, variable, lat=lat, lon=lon, selectors=selectors)
    # Float64 retains decoded scale/offset precision; NaN is the output nodata.
    values[~np.isfinite(values)] = np.nan
    with tempfile.TemporaryDirectory(dir=destination.parent) as folder:
        temporary = Path(folder) / "result.tif"
        with rasterio.open(temporary, "w", driver="GTiff", height=values.shape[0],
                           width=values.shape[1], count=1, dtype="float64", crs="EPSG:4326",
                           transform=transform, nodata=np.nan, compress="deflate") as output:
            output.write(values, 1)
            output.update_tags(source_variable=variable, AREA_OR_POINT="Area")
        with rasterio.open(temporary) as result:
            if result.crs.to_epsg() != 4326 or result.transform != transform:
                raise RuntimeError("GeoTIFF georeferencing verification failed")
            np.testing.assert_array_equal(result.read(1), values)
        if destination.exists() and not overwrite:
            raise FileExistsError(destination)
        temporary.replace(destination)
    return {"output": str(destination), "shape": list(values.shape), "crs": "EPSG:4326",
            "valid_cells": int(np.isfinite(values).sum()), "verified": True}
