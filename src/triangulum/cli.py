import argparse

from triangulum.api import TriangulumClient
from triangulum.fs import init_triangulum_fs
from triangulum.logger import init_logger


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="triangulum",
        usage="triangulum <lat> <lon> [option]...",
        description="Estimate climate normals in CONUS using nearby station data",
        epilog="Copyright (c) 2023-2026 Addison Kline (GitHub: @addisonkline)",
    )
    parser.add_argument(
        "lat", type=float, help="the latitude, in decimal degrees (e.g. 38.8)"
    )
    parser.add_argument(
        "lon", type=float, help="the longitude, in decimal degrees (e.g. -90.6)"
    )
    parser.add_argument(
        "-i",
        "--imperial",
        action="store_true",
        help="use imperial units rather than metric",
    )
    parser.add_argument(
        "-llf",
        "--log-level-file",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="the minimum log level to write to the log file (default = 'INFO')",
    )
    parser.add_argument(
        "-llc",
        "--log-level-console",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="the minimum log level to write to the console (default = 'INFO')",
    )
    parser.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help="print plain text rather than rich text",
    )

    args = parser.parse_args()

    init_triangulum_fs()

    init_logger(
        log_level_console=args.log_level_console,
        log_level_file=args.log_level_file,
        plain=args.plain,
    )

    client = TriangulumClient(imperial_units=args.imperial)

    result = client.get_coords_normals(latitude=args.lat, longitude=args.lon)
    if args.plain:
        print(result.pretty())
    else:
        result.rich_print()
