"""Create a tiny synthetic NetCDF3 file; no external dataset is needed."""
from pathlib import Path
import numpy as np
import xarray as xr

target = Path(__file__).with_name("sample.nc")
ds = xr.Dataset({"temperature": (("time", "lat", "lon"),
                                np.array([[[10., 11., 12.], [20., np.nan, 22.]],
                                          [[13., 14., 15.], [23., 24., 25.]]]))},
                coords={"time": [0, 1], "lat": [45., 46.], "lon": [7., 8., 9.]})
ds.lat.attrs["units"] = "degrees_north"
ds.lon.attrs["units"] = "degrees_east"
ds.temperature.attrs["units"] = "degree_Celsius"
ds.to_netcdf(target, engine="scipy", format="NETCDF3_CLASSIC")
print(target)
