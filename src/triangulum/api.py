import json
from math import exp, sqrt

import httpx

from triangulum.types import ClimateNormalMonth, ClimateNormals, ClimateNormalsEstimate, StationInfo
from triangulum.utils import get_current_version


ELEVATION_API = "https://epqs.nationalmap.gov/v1/json"
CLIMATE_API = "https://www.ncei.noaa.gov/access/services/data/v1"
# ?dataset=normals-monthly-1991-2020&stations={station_id}&startDate=2022-01-01&endDate=2022-12-31&format=json
STATIONS_API = "https://www.ncei.noaa.gov/access/services/search/v1/data"

MONTH_STRS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]


class TriangulumClient:
    """
    Synchronous client for the Triangulum API.
    """

    def __init__(
        self,
        imperial_units: bool = False,
    ) -> None:
        self.imperial = imperial_units

        self._client = httpx.Client(
            headers={
                "User-Agent": f"triangulum/{get_current_version()} (https://github.com/addisonkline/triangulum)"
            },
            timeout=60,
        )
    
    def get_coords_normals(
        self,
        latitude: float,
        longitude: float,
    ) -> ClimateNormalsEstimate:
        # basic station info
        stations = self._get_coords_stations(
            latitude=latitude,
            longitude=longitude
        )

        # nearby stations and their distances
        distances = self._get_station_distances(
            stations=stations,
            latitude=latitude,
            longitude=longitude
        )
        weights = self._get_station_weights(
            distances=distances
        )

        # nearby station normals
        nearby_normals = self._get_station_normals(
            station_ids=[v.id for _k, v in stations.items()]
        )

        #print(distances)
        #print(weights)
        print(nearby_normals)

        raise NotImplementedError
    
    def _get_coords_elev(
        self,
        latitude: float,
        longitude: float,
    ) -> float:
        response = self._client.get(
            url=ELEVATION_API,
            params={
                "x": longitude,
                "y": latitude,
                "unit": "Feet" if self.imperial else "Meters",
                "includeDate": False,
            }
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"elevation API returned non-OK status code: {response.status_code}"
            )
        
        json_response = response.json()

        elev = json_response.get("value")
        if elev is None:
            raise RuntimeError(
                "elevation API did not return value as expected"
            )
        
        return float(elev)
    
    def _get_coords_stations(
        self,
        latitude: float,
        longitude: float
    ) -> dict[str, StationInfo]:
        bbox: tuple[float, float, float, float] = (
            latitude + 1, # north
            longitude - 1, # west
            latitude - 1, # south
            longitude + 1 # east
        )

        response = self._client.get(
            url=STATIONS_API,
            params={
                "dataset": "normals-monthly",
                "startDate": "1991-01-01",
                "endDate": "2020-12-31",
                "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            }
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"stations API returned non-OK status code: {response.status_code}: {response.text}"
            )
        
        stations = response.json()

        resp_results = stations.get("results")
        station_info: dict[str, StationInfo] = {}
        for result in resp_results:
            station = result.get("stations")[0]
            station_id = station.get("id")
            station_name = station.get("name")
            lat = result.get("centroid").get("point")[1]
            lon = result.get("centroid").get("point")[0]

            stn = StationInfo(
                id=station_id,
                name=station_name,
                lat=lat,
                lon=lon,
                elev=-1.0,
            )

            station_info.update({station_id: stn})

        return station_info

    def _get_station_normals(
        self,
        station_ids: list[str]
    ) -> dict[str, ClimateNormals]:
        stations_str = ",".join(station_ids)
        unit_str = "standard" if self.imperial else "metric"

        response = self._client.get(
            url=CLIMATE_API,
            params={
                "dataset": "normals-monthly",
                "stations": stations_str,
                "startDate": "1991-01-01",
                "endDate": "2020-12-31",
                "format": "json",
                "dataTypes": "MLY-PRCP-NORMAL,MLY-TMAX-NORMAL,MLY-TAVG-NORMAL,MLY-TMIN-NORMAL",
                "units": unit_str,
            }
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"normals API returned non-OK status code: {response.status_code}: {response.text}"
            )
        
        response_json = response.json()

        station_normals_dict: dict[str, ClimateNormals] = {}
        for station_id in station_ids:
            station_normals = [item for item in response_json if item.get("STATION") == station_id]
            monthly_normals: list[ClimateNormalMonth] = []
            for month in MONTH_STRS:
                monthly_normal = [item for item in station_normals if item.get("DATE") == month][0]
                
                mly_tmax_normal = monthly_normal.get("MLY-TMAX-NORMAL")
                if mly_tmax_normal is None:
                    continue
                mly_tavg_normal = monthly_normal.get("MLY-TAVG-NORMAL")
                if mly_tavg_normal is None:
                    continue
                mly_tmin_normal = monthly_normal.get("MLY-TMIN-NORMAL")
                if mly_tmin_normal is None:
                    continue
                mly_prcp_normal = monthly_normal.get("MLY-PRCP-NORMAL")
                if mly_prcp_normal is None:
                    continue

                monthly_normal_obj = ClimateNormalMonth(
                    month=int(month),
                    temp_daily_max=mly_tmax_normal,
                    temp_daily_mean=mly_tavg_normal,
                    temp_daily_min=mly_tmin_normal,
                    precip_monthly_mean=mly_prcp_normal,
                )
                monthly_normals.append(monthly_normal_obj)

            station_normals_obj = ClimateNormals.from_monthly(monthly_normals)
            station_normals_dict.update({station_id: station_normals_obj})

        return station_normals_dict
    
    def _get_station_distances(
        self,
        stations: dict[str, StationInfo],
        latitude: float,
        longitude: float,
    ) -> dict[str, float]:
        distances: dict[str, float] = {}

        for station_id, station in stations.items():
            distance = sqrt((latitude - station.lat)**2 + (longitude - station.lon)**2)
            distances.update({station_id: distance})

        return distances
    
    def _get_station_weights(
        self,
        distances: dict[str, float]
    ) -> dict[str, float]:
        return {station_id: exp(distance) for station_id, distance in distances.items()}
    
    def _get_coords_normals(
        self,
        normals: dict[str, ClimateNormals],
        weights: dict[str, float]
    ) -> ClimateNormals:
        raise NotImplementedError
