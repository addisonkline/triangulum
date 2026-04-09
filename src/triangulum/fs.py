import os
from pathlib import Path


def init_triangulum_fs() -> None:
    """
    Create the necessary files and directories for Triangulum in the local file system.
    """
    TRIANGULUM_BASE = Path(".triangulum")
    TRIANGULUM_LOGS = TRIANGULUM_BASE / "logs"
    TRIANGULUM_CACHE = TRIANGULUM_BASE / "cache"

    os.makedirs(TRIANGULUM_BASE, exist_ok=True)
    os.makedirs(TRIANGULUM_LOGS, exist_ok=True)
    os.makedirs(TRIANGULUM_CACHE, exist_ok=True)

    # cache internals
    # manifest
    MANIFEST_FILE = TRIANGULUM_CACHE / "manifest.lock"
    if not MANIFEST_FILE.exists():
        with open(".triangulum/cache/manifest.lock", "w") as manifile:
            manifile.write("{}")
