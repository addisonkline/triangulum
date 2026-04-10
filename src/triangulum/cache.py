import json
import uuid
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


class CachedStationNormals(CacheEntry):
    value: dict[str, ClimateNormals]


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
                match req_type:
                    case "_get_station_normals":
                        self._cache_insert_station_normals(result, **kwargs)
                    case "_get_coords_stations":
                        self._cache_insert_coords_stations(result, **kwargs)
                    case _:
                        raise ValueError(f"invalid operation: {req_type}")

            return result

        return wrapper

    def _cache_insert_station_normals(
        self, result: dict[str, ClimateNormals], station_ids: list[str]
    ) -> None:
        """
        Insert a new station normals entry into the cache.
        """
        logger.info(
            f"attempting cache insert: _get_station_normals: station_ids = {station_ids}"
        )

        entry_id = str(uuid.uuid4())
        entry_key = "&".join(station_ids)

        # write cache entry
        cache_entry_path = self.cache_root / f"{entry_id}._get_station_normals"
        with open(cache_entry_path, "w") as cachefile:
            entry_obj = CachedStationNormals(
                key=entry_key, value=result, timestamp=datetime.now(timezone.utc)
            )
            cachefile.write(entry_obj.model_dump_json())

        # update manifest file
        manifest_file_path = self.cache_root / "manifest.lock"
        with open(manifest_file_path, "a") as manifile:
            new_entry = entry_key + "=" + entry_id + "\n"
            manifile.writelines(new_entry)

        logger.info(
            f"cache insert successful: _get_station_normals: station_ids = {station_ids}"
        )

    def _cache_insert_coords_stations(
        self, result: dict[str, StationInfo], latitude: float, longitude: float
    ) -> None:
        """
        Insert a new coordinates stations entry into the cache.
        """

        logger.info(
            f"attempting cache insert: _get_coords_stations: lat = {latitude}, lon = {longitude}"
        )

        lat_key = str(latitude)[:5]
        lon_key = str(longitude)[:5]

        entry_id = str(uuid.uuid4())
        entry_key = f"_get_coords_stations&{lat_key}&{lon_key}"

        # write cache entry
        cache_entry_path = self.cache_root / f"{entry_id}._get_coords_stations"
        with open(cache_entry_path, "w") as cachefile:
            entry_obj = CachedCoordsStations(
                key=entry_key, value=result, timestamp=datetime.now(timezone.utc)
            )
            cachefile.write(entry_obj.model_dump_json())

        # update manifest file
        manifest_file_path = self.cache_root / "manifest.lock"
        with open(manifest_file_path, "a") as manifile:
            new_entry = entry_key + "=" + entry_id + "\n"
            manifile.writelines(new_entry)

        logger.info(
            f"cache insert successful: _get_coords_stations: lat = {latitude}, lon = {longitude}"
        )

    def _handle_station_normals(
        self, station_ids: list[str]
    ) -> dict[str, ClimateNormals] | None:
        """
        Handle a cache request for station normals.
        """
        logger.debug(
            f"handling _get_station_normals request for station IDs: {station_ids}"
        )

        ids_key = "&".join([id for id in station_ids])

        result = self._get_station_normals_or_none(ids_key=ids_key)

        return result

    def _get_station_normals_or_none(
        self, ids_key: str
    ) -> dict[str, ClimateNormals] | None:
        """
        Attempt to get a specific cache entry for _get_station_normals, if one exists.
        """
        manifest_file = self.cache_root / "manifest.lock"
        request_type_key = "_get_station_normals"
        manifest_key = request_type_key + "&" + ids_key

        with open(manifest_file) as manifile:
            manifest_entries = manifile.readlines()
            manifest_entries_obj = {
                entry.split("=")[0]: entry.split("=")[1] for entry in manifest_entries
            }
            if manifest_key in manifest_entries_obj:
                manifest_entry_path = (
                    manifest_entries_obj[manifest_key].strip() + "._get_station_normals"
                )
                cached_file = self.cache_root / manifest_entry_path
                with open(cached_file) as cachefile:
                    cachefile_content = cachefile.read()
                    cachefile_content_obj = json.loads(cachefile_content)
                    logger.info(f"cache hit: {ids_key}")
                    return CachedStationNormals.model_validate(
                        cachefile_content_obj
                    ).value
            else:
                logger.info(f"cache miss: {ids_key}")
                return None

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

        lat_key = str(latitude)[:5]
        lon_key = str(longitude)[:5]

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
            manifest_entries = manifile.readlines()
            manifest_entries_obj = {
                entry.split("=")[0]: entry.split("=")[1] for entry in manifest_entries
            }
            if manifest_key in manifest_entries_obj:
                manifest_entry_path = (
                    manifest_entries_obj[manifest_key].strip() + "._get_coords_stations"
                )
                cached_file = self.cache_root / manifest_entry_path
                with open(cached_file) as cachefile:
                    cachefile_content = cachefile.read()
                    cachefile_content_obj = json.loads(cachefile_content)
                    logger.info(f"cache hit: {manifest_key}")
                    return CachedCoordsStations.model_validate(
                        cachefile_content_obj
                    ).value
            else:
                logger.info(f"cache miss: {manifest_key}")
                return None
