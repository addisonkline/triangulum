import json
from datetime import datetime, timezone
from functools import wraps
from logging import getLogger
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from triangulum.types import ClimateNormals, StationInfo

logger = getLogger(__name__)


class CacheEntry(BaseModel):
    key: str
    value: Any
    timestamp: datetime


class CachedCoordsStations(CacheEntry):
    value: dict[str, StationInfo]


class TriangulumCache:
    """
    Filesystem cache for API requests.
    """

    def __init__(self) -> None:
        self.cache_root = Path(".triangulum") / "cache"

    def check(
        self,
        func,
    ):
        """
        Decorator to apply on operations where the cache should be checked for the given query,
        and inserted if not already present.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            req_type = func.__name__
            logger.debug(f"function name: {req_type}")
            logger.debug(f"function args: {args}")
            logger.debug(f"function kwargs: {kwargs}")

            match req_type:
                case "_get_station_normals":
                    result = self._handle_station_normals(**kwargs)
                case "_get_coords_stations":
                    result = self._handle_coords_stations(**kwargs)
                case _:
                    raise ValueError(f"invalid operation: {req_type}")

            if result is None:
                result = func(*args, **kwargs)
                self._cache_insert(result, req_type, **kwargs)

            return result

        return wrapper

    def _cache_insert(
        self,
        result: Any,
        req_type: str,
        **kwargs: Any,
    ) -> None:
        """
        Insert a new entry into the cache.
        """
        manifest_key = "&".join([req_type])
        for k, v in kwargs.items():
            manifest_key += f"&{v}"
        cache_filepath = self.cache_root / manifest_key

        if isinstance(result, StationInfo):
            result_obj = result.model_dump()
        else:
            result_obj = json.dumps(result)

        with open(cache_filepath, "w") as cachefile:
            cachefile.write(
                json.dumps(
                    {
                        "key": manifest_key,
                        "value": result_obj,
                        "timestamp": datetime.now(timezone.utc),
                    }
                )
            )

        # update manifest file
        manifest_file = self.cache_root / "manifest.lock"
        with open(manifest_file, "+") as manifile:
            manifest_content = manifile.read()
            manifest_content_obj = json.loads(manifest_content)
            manifest_content_obj.update({manifest_key, cache_filepath})
            manifile.write(json.dumps(manifest_content_obj))

    def _handle_station_normals(
        self, station_ids: list[str]
    ) -> dict[str, ClimateNormals] | None:
        """
        Handle a cache request for station normals.
        """
        logger.debug(
            f"handling _get_station_normals request for station IDs: {station_ids}"
        )

        raise NotImplementedError

    def _handle_coords_stations(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, StationInfo] | None:
        """
        Attempt to get a specific cache entry for _get_coords_stations, if one exists.
        """
        logger.debug(
            f"handling _get_coords_stations request for lat = {latitude}, lot = {longitude}"
        )

        lat_key = str(latitude)[:4]
        lon_key = str(longitude)[:4]

        result = self._get_coords_stations_or_none(
            lat_key=lat_key,
            lon_key=lon_key,
        )
        return result

    def _get_coords_stations_or_none(
        self,
        lat_key: str,
        lon_key: str,
    ) -> dict[str, StationInfo] | None:
        """
        Attempt to get a specific cache entry for _get_coords_stations, if one exists.
        """
        manifest_file = self.cache_root / "manifest.lock"
        request_type_key = "_get_coords_stations"
        manifest_key = "&".join([request_type_key, lat_key, lon_key])

        with open(manifest_file) as manifile:
            manifest_content = manifile.read()
            manifest_content_obj = json.loads(manifest_content)
            if manifest_key in manifest_content_obj:
                cached_file = manifest_content_obj[manifest_key]
                with open(cached_file) as cachefile:
                    cachefile_content = cachefile.read()
                    cachefile_content_obj = json.loads(cachefile_content)
                    return CachedCoordsStations.model_validate(
                        cachefile_content_obj
                    ).value
            else:
                return None
