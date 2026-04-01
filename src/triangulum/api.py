import json
from math import exp, sqrt

import httpx

from triangulum.consts import MONTH_STRS
from triangulum.types import ClimateNormalMonth, ClimateNormals, ClimateNormalsEstimate, StationEstimateInfo, StationInfo
from triangulum.utils import get_current_version


ELEVATION_API = "https://epqs.nationalmap.gov/v1/json"
CLIMATE_API = "https://www.ncei.noaa.gov/access/services/data/v1"
# ?dataset=normals-monthly-1991-2020&stations={station_id}&startDate=2022-01-01&endDate=2022-12-31&format=json
STATIONS_API = "https://www.ncei.noaa.gov/access/services/search/v1/data"


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
        estimate_info = self._build_station_estimate_info(
            stations=stations,
            distances=distances,
            weights=weights
        )

        # nearby station normals
        nearby_normals = self._get_station_normals(
            station_ids=[v.id for _k, v in stations.items()]
        )

        # print(distances)
        # print(weights)

        normals_estimate = self._get_coords_normals(
            normals=nearby_normals,
            weights=weights
        )

        # print(normals_estimate)

        normals_estimate_final = ClimateNormalsEstimate(
            temp_daily_mean=normals_estimate.temp_daily_mean,
            temp_daily_max=normals_estimate.temp_daily_max,
            temp_daily_min=normals_estimate.temp_daily_min,
            precip_monthly_mean=normals_estimate.precip_monthly_mean,
            stations=estimate_info
        )

        return normals_estimate_final
    
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
        exps = {station_id: exp(distance) for station_id, distance in distances.items()}
        exps_sum = float(sum(exps.values()))
        weights = {k: v / exps_sum for k, v in exps.items()}

        return weights
    
    def _get_coords_normals(
        self,
        normals: dict[str, ClimateNormals],
        weights: dict[str, float]
    ) -> ClimateNormals:
        station_normals: dict[str, ClimateNormals] = {}
        for station_id in normals:
            normal = normals[station_id]
            weight = weights[station_id]
            mly_tmax_normals = {k: weight * v for k, v in normal.temp_daily_max.items()}
            mly_tavg_normals = {k: weight * v for k, v in normal.temp_daily_mean.items()}
            mly_tmin_normals = {k: weight * v for k, v in normal.temp_daily_min.items()}
            mly_prcp_normals = {k: weight * v for k, v in normal.precip_monthly_mean.items()}
            norms = ClimateNormals(
                temp_daily_max=mly_tmax_normals,
                temp_daily_mean=mly_tavg_normals,
                temp_daily_min=mly_tmin_normals,
                precip_monthly_mean=mly_prcp_normals
            )
            station_normals.update({station_id: norms})

        key_months: list[str] = MONTH_STRS

        agg_mly_tmax_normals = {k: v.temp_daily_max for k, v in station_normals.items()}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_tmax_normals = {month: sum([v.get(int(month)) for _k, v in agg_mly_tmax_normals.items()]) for month in key_months}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_tavg_normals = {k: v.temp_daily_mean for k, v in station_normals.items()}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_tavg_normals = {month: sum([v.get(int(month)) for _k, v in agg_mly_tavg_normals.items()]) for month in key_months}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_tmin_normals = {k: v.temp_daily_min for k, v in station_normals.items()}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_tmin_normals = {month: sum([v.get(int(month)) for _k, v in agg_mly_tmin_normals.items()]) for month in key_months}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_prcp_normals = {k: v.precip_monthly_mean for k, v in station_normals.items()}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))
        agg_mly_prcp_normals = {month: sum([v.get(int(month)) for _k, v in agg_mly_prcp_normals.items()]) for month in key_months}
        # print("=" * 60)
        # print(json.dumps(agg_mly_tmax_normals, indent=4))

        return ClimateNormals(
            temp_daily_mean=agg_mly_tavg_normals,
            temp_daily_max=agg_mly_tmax_normals,
            temp_daily_min=agg_mly_tmin_normals,
            precip_monthly_mean=agg_mly_prcp_normals
        )
    
    def _build_station_estimate_info(
        self,
        stations: dict[str, StationInfo],
        distances: dict[str, float],
        weights: dict[str, float]
    ) -> dict[str, StationEstimateInfo]:
        estimate_info_dict: dict[str, StationEstimateInfo] = {}
        for station_id, station_info in stations.items():
            estimate_info = StationEstimateInfo(
                id=station_id,
                name=station_info.name,
                lat=station_info.lat,
                lon=station_info.lon,
                elev=station_info.elev,
                distance=distances[station_id],
                weight=weights[station_id]
            )
            estimate_info_dict.update({station_id: estimate_info})
        return estimate_info_dict

