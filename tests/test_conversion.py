import gzip
import numpy as np
import pytest
import rasterio
import xarray as xr
from nc2tiff import convert, prepare_grid
from nc2tiff.cli import main


def dataset(lat=(45., 46.), lon=(7., 8., 9.)):
    return xr.Dataset({"rain": (("lat", "lon"), [[1., 2., 3.], [4., np.nan, 6.]])},
                      coords={"lat": list(lat), "lon": list(lon)})


@pytest.mark.parametrize("flip_y,flip_x", [(False, False), (True, False), (False, True), (True, True)])
def test_orientation_bounds_and_values(tmp_path, flip_y, flip_x):
    ds = dataset()
    if flip_y:
        ds = ds.isel(lat=slice(None, None, -1))
    if flip_x:
        ds = ds.isel(lon=slice(None, None, -1))
    source, output = tmp_path / "input.nc", tmp_path / "output.tif"
    ds.to_netcdf(source, engine="scipy")
    assert convert(source, output, "rain")["verified"]
    with rasterio.open(output) as result:
        np.testing.assert_array_equal(result.read(1), [[4., np.nan, 6.], [1., 2., 3.]])
        assert tuple(result.bounds) == (6.5, 44.5, 9.5, 46.5)
        assert result.crs.to_epsg() == 4326
        assert np.isnan(result.nodata)
    with pytest.raises(FileExistsError):
        convert(source, output, "rain")


def test_packed_values_and_gzip(tmp_path):
    source, output = tmp_path / "packed.nc", tmp_path / "out.tif"
    dataset().to_netcdf(source, engine="scipy", encoding={"rain": {"dtype": "int16", "scale_factor": .5, "_FillValue": -9999}})
    compressed = tmp_path / "packed.nc.gz"
    compressed.write_bytes(gzip.compress(source.read_bytes()))
    convert(compressed, output, "rain")
    with rasterio.open(output) as result:
        np.testing.assert_array_equal(result.read(1), [[4., np.nan, 6.], [1., 2., 3.]])


def test_requires_explicit_time_and_handles_transpose():
    ds = dataset().expand_dims(time=[0, 1]).transpose("lon", "time", "lat")
    with pytest.raises(ValueError, match="non-spatial"):
        prepare_grid(ds, "rain")
    values, _ = prepare_grid(ds, "rain", selectors={"time": 1})
    assert values.shape == (2, 3)


def test_rejects_irregular_and_curvilinear():
    with pytest.raises(ValueError, match="regularly"):
        prepare_grid(dataset(lon=(7., 8., 10.)), "rain")
    ds = dataset().rename({"lat": "y", "lon": "x"})
    ds["lat"] = (("y", "x"), [[45., 45.1, 45.], [46., 46., 46.]])
    ds["lon"] = (("y", "x"), [[7., 8., 9.], [7., 8., 9.]])
    with pytest.raises(ValueError, match="Curvilinear"):
        prepare_grid(ds, "rain")


def test_rectilinear_2d_and_bad_units():
    ds = dataset().rename({"lat": "y", "lon": "x"})
    ds["lat"] = (("y", "x"), [[45., 45., 45.], [46., 46., 46.]])
    ds["lon"] = (("y", "x"), [[7., 8., 9.], [7., 8., 9.]])
    assert prepare_grid(ds, "rain")[0][0, 0] == 4
    ds.lon.attrs["units"] = "metres"
    with pytest.raises(ValueError, match="degrees"):
        prepare_grid(ds, "rain")


def test_cli(tmp_path, capsys):
    source = tmp_path / "input.nc"
    dataset().to_netcdf(source, engine="scipy")
    assert main([str(source), "--list"]) == 0
    assert '"rain"' in capsys.readouterr().out
    assert main([str(source), str(tmp_path / "out.tif"), "--variable", "rain"]) == 0
    assert main([str(source), str(tmp_path / "other.tif"), "--variable", "missing"]) == 2


def test_netcdf4_input(tmp_path):
    source = tmp_path / "input.nc"
    output = tmp_path / "output.tif"
    dataset().to_netcdf(source, engine="h5netcdf")
    assert convert(source, output, "rain")["valid_cells"] == 5
