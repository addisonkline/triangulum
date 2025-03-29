"""
triangulum/utils/calculator.py
Created by Addison Kline in March 2023
"""
# external imports
import requests
import pandas as pd
import numpy as np
from scipy.stats import norm
# internal imports
from triangulum.models import (
    Station
)

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS_BY_MONTH = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def get_location_elev(metric: bool, lat: float, lon: float) -> float:
    """
    Get the elevation for the given coordinates using the USGS API.
    `metric` specifies whether the result is in meters or feet.
    """
    unit = "Meters" if metric else "Feet"
    
    elev_response = requests.get(f'https://epqs.nationalmap.gov/v1/json?x={lon}&y={lat}&units={unit}&wkid=4326&includeDate=False').json() # usgs inverts latitude and longitude interestingly enough
    input_elev = float(elev_response["value"]) # because the API returns a string when using meters for some reason

    return input_elev

def get_location_nearest_stations(lat: float, lon: float) -> list[Station]:
    """
    Given a (validated) set of coordinates, return the 3 closest weather stations and their coordinate distances.
    """
    stations = pd.read_json('weather_stations.json')

    stations["distance"] = np.sqrt((lat - stations["lat"])**2 + (lon - stations["long"])**2)
    closest_stations = stations.sort_values(by="distance", ascending=True).iloc[0:3]

    # convert df into list[Station]
    closest_stations_list: list[Station] = []
    for i in range(3):
        station_this_series = closest_stations.iloc[i]
        station_this = Station(
            id=station_this_series.get('id'),
            lat=station_this_series.get('lat'),
            lon=station_this_series.get('lon'),
            elev=station_this_series.get('elev'),
            city=station_this_series.get('city'),
            state=station_this_series.get('state'),
            country=station_this_series.get('country'),
            distance_from_loc=station_this_series.get('distance')
        )
        closest_stations_list.append(station_this)
    
    return closest_stations_list

def get_normals_from_station(station: Station) -> pd.DataFrame:
    """
    Given a Station object, fetch and compile the climate normals for that station.
    """
    url = f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=normals-monthly-1991-2020&stations={station.id}&startDate=2022-01-01&endDate=2022-12-31&format=json"
    response = requests.get(url)
    json_data = response.json()

    max_temp_normals = []
    min_temp_normals = []
    precip_normals = []
    max_temp_std = []
    min_temp_std = []

    for month in range (12):
        max_temp_normals.append(json_data[month]['MLY-TMAX-NORMAL'])
        min_temp_normals.append(json_data[month]['MLY-TMIN-NORMAL'])
        precip_normals.append(json_data[month]['MLY-PRCP-NORMAL'])
        max_temp_std.append(json_data[month]['MLY-TMAX-STDDEV'])
        min_temp_std.append(json_data[month]['MLY-TMIN-STDDEV'])

    return pd.DataFrame({
        "month": MONTHS,
        "tmax": max_temp_normals,
        "tmin": min_temp_normals,
        "precip": precip_normals,
        "tmax_std": max_temp_std,
        "tmin_std": min_temp_std
    })

def get_location_normals(lat: float, lon: float) -> pd.DataFrame:
    """
    Given a set of (validated) coordinates, return a DataFrame containing estimated normals based on a weighted average of the 3 closest stations.
    """
    nearest_stations = get_location_nearest_stations(lat, lon)
    distances = [station.distance_from_loc for station in nearest_stations]
    distance_sum = distances[0] + distances[1] + distances[2]
    station_normals = [get_normals_from_station(station) for station in nearest_stations]

    # determine weights to use based on station distances
    # these are all linear weights between 0 and 1 s.t. w1 + w2 + w3 = 1
    WEIGHT_1 = (1 - (distances[0]/distance_sum)) / 2
    WEIGHT_2 = (1 - (distances[1]/distance_sum)) / 2
    WEIGHT_3 = (1 - (distances[2]/distance_sum)) / 2

    return pd.DataFrame({
        "months": MONTHS,
        "tmax": WEIGHT_1*station_normals[0]['tmax'] + WEIGHT_2*station_normals[1]['tmax'] + WEIGHT_3*station_normals[2]['tmax'],    
        "tmin": WEIGHT_1*station_normals[0]['tmin'] + WEIGHT_2*station_normals[1]['tmin'] + WEIGHT_3*station_normals[2]['tmin'],
        "precip": WEIGHT_1*station_normals[0]['precip'] + WEIGHT_2*station_normals[1]['precip'] + WEIGHT_3*station_normals[2]['precip'],
        "tmax_std": WEIGHT_1*station_normals[0]['tmax_std'] + WEIGHT_2*station_normals[1]['tmax_std'] + WEIGHT_3*station_normals[2]['tmax_std'],
        "tmin_std": WEIGHT_1*station_normals[0]['tmin_std'] + WEIGHT_2*station_normals[1]['tmin_std'] + WEIGHT_3*station_normals[2]['tmin_std'],
    })

def get_location_normal_probs(lat: float, lon: float) -> pd.DataFrame:
    """
    Given a set of (validated) coordinates, determine the normal probability table based on the estimated normals.
    """
    normals = get_location_normals(lat, lon)

    return pd.DataFrame({
        "month": MONTHS,
        "tmax_p95": norm.ppf(0.95, normals['tmax'], normals['tmax_std']),
        "tmax_p75": norm.ppf(0.75, normals['tmax'], normals['tmax_std']),
        "tmax_p25": norm.ppf(0.25, normals['tmax'], normals['tmax_std']),
        "tmax_p05": norm.ppf(0.05, normals['tmax'], normals['tmax_std']),
        "tmin_p95": norm.ppf(0.95, normals['tmin'], normals['tmin_std']),
        "tmin_p75": norm.ppf(0.75, normals['tmin'], normals['tmin_std']),
        "tmin_p25": norm.ppf(0.25, normals['tmin'], normals['tmin_std']),
        "tmin_p05": norm.ppf(0.05, normals['tmin'], normals['tmin_std'])
    })

def get_location_occurrence_probs(metric: bool, lat: float, lon: float) -> pd.DataFrame:
    """
    Given a set of (validated) coordinates, determine the occurrence probability table based on the estimated normals.
    """
    normals = get_location_normals(lat, lon)

    if metric:
        return pd.DataFrame({
            "month": MONTHS,
            "prob_max_geq_40C": 1 - norm.cdf(40, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_max_geq_30C": 1 - norm.cdf(30, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_max_geq_20C": 1 - norm.cdf(20, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_max_geq_10C": 1 - norm.cdf(10, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_10C": norm.cdf(10, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_0C": norm.cdf(0, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_-10C": norm.cdf(-10, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_-20C": norm.cdf(-20, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH)))
        })
    else:
        return pd.DataFrame({
            "month": MONTHS,
            "prob_max_geq_40C": 1 - norm.cdf(104, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_max_geq_30C": 1 - norm.cdf(86, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_max_geq_20C": 1 - norm.cdf(68, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_max_geq_10C": 1 - norm.cdf(50, normals['tmax'], (normals['tmax_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_10C": norm.cdf(50, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_0C": norm.cdf(32, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_-10C": norm.cdf(14, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH))),
            "prob_min_leq_-20C": norm.cdf(-4, normals['tmin'], (normals['tmin_std'] * np.sqrt(DAYS_BY_MONTH)))
        })

def f_to_c(temps: pd.Series) -> pd.Series:
    """
    Convert a series of Fahrenheit temps to Celsius.
    """
    return (temps - 32) * (5/9)

def c_to_f(temps: pd.Series) -> pd.Series:
    """
    Convert a series of Celsius temps to Fahrenheit.
    """
    return ((9/5) * temps) + 32

def in_to_mm(precips: pd.Series) -> pd.Series:
    """
    Convert a series of precip totals in inches to millimeters.
    """
    return precips * 25.4

def mm_to_in(precips: pd.Series) -> pd.Series:
    """
    Convert a series of precip totals in millimeters to inches.
    """
    return precips / 25.4

def normals_imperial_to_metric(normals: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a DataFrame of normals in imperial units to corresponding one using metric units.
    """
    return pd.DataFrame({
        "month": MONTHS,
        "tmax": f_to_c(normals['tmax']),
        "tmin": f_to_c(normals['tmin']),
        "precip": in_to_mm(normals['precip']),
        "tmax_std": f_to_c(normals['tmax_std']),
        "tmin_std": f_to_c(normals['tmin_std'])
    })

def normals_metric_to_imperial(normals: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a DataFrame of normals in metric units to corresponding one using imperial units.
    """
    return pd.DataFrame({
        "month": MONTHS,
        "tmax": c_to_f(normals['tmax']),
        "tmin": c_to_f(normals['tmin']),
        "precip": mm_to_in(normals['precip']),
        "tmax_std": c_to_f(normals['tmax_std']),
        "tmin_std": c_to_f(normals['tmin_std'])
    })