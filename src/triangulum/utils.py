from importlib import metadata


def get_current_version() -> str:
    return metadata.version("triangulum")