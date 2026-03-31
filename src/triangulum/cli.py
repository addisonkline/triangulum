import argparse

from triangulum.api import TriangulumClient


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="triangulum",
        usage="triangulum <lat> <lon> [option]...",
        description="Estimate climate normals in CONUS using nearby station data",
        epilog="Copyright (c) 2023-2026 Addison Kline (GitHub: @addisonkline)"
    )
    parser.add_argument(
        "lat",
        type=float,
        help="the latitude, in decimal degrees (e.g. 38.8)"
    )
    parser.add_argument(
        "lon",
        type=float,
        help="the longitude, in decimal degrees (e.g. -90.6)"
    )
    parser.add_argument(
        "-i",
        "--imperial",
        action="store_true",
        help="use imperial units rather than metric"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="include more detailed process output"
    )

    args = parser.parse_args()

    client = TriangulumClient()

    result = client.get_coords_normals(
        latitude=args.lat,
        longitude=args.lon
    )
    print(result)