import argparse
import json
import sys

from .convert import convert, open_dataset


def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert a regular WGS84 NetCDF grid to GeoTIFF")
    parser.add_argument("input")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--variable")
    parser.add_argument("--list", action="store_true", help="List data variables and dimensions")
    parser.add_argument("--lat", default="lat")
    parser.add_argument("--lon", default="lon")
    parser.add_argument("--isel", action="append", default=[], metavar="DIM=INDEX")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.list:
            with open_dataset(args.input) as ds:
                print(json.dumps({n: dict(ds[n].sizes) for n in ds.data_vars}, indent=2))
            return 0
        if not args.output or not args.variable:
            parser.error("output and --variable are required unless --list is used")
        selectors = {}
        for item in args.isel:
            dim, index = item.rsplit("=", 1)
            if dim in selectors:
                raise ValueError(f"Duplicate selector: {dim}")
            selectors[dim] = int(index)
        print(json.dumps(convert(args.input, args.output, args.variable, lat=args.lat,
                                 lon=args.lon, selectors=selectors, overwrite=args.overwrite), indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"nc2tiff: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
