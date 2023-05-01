import numpy as np
import pandas as pd
import time
import requests
import calculator
import koppen
import trewartha
#from geopy import distance

version = 1.3
normal_period = "1991-2020"

# Input coordinates and corresponding elevation
#(38.4500, -90.0060) St. Louis
#(40.7128, -74.0060) NYC
input_coords = (38.6488, -90.3106)
elev_response = requests.get(f'https://epqs.nationalmap.gov/v1/json?x={input_coords[1]}&y={input_coords[0]}&units=Feet&wkid=4326&includeDate=False').json() # usgs inverts latitude and longitude interestingly enough
input_elev = elev_response["value"]

# TODO: make this better
lapse = 3.56

# Load weather station data
station_data = pd.read_json("weather_stations.json")

# create name attribute
station_data['name'] = station_data['city'] + ", " + station_data['state'] + ", " + station_data['country']

# Calculate distances between input coordinates and weather stations
"""
distances_list = []
for i in range (10):
    station_coords = (station_data.loc[i, 'lat'], station_data.loc[i, 'long'])
    distances_list.append(distance.distance(input_coords, (station_data.loc[i, 'lat'], station_data.loc[i, 'long'])).miles)
distances = np.array(distances_list)
"""
# geopy was being a pain with distances between places of different altitudes
distances = np.sqrt((station_data['lat'] - input_coords[0]) ** 2 + (station_data['long'] - input_coords[1]) ** 2)

# Get indices of the three nearest weather stations
nearest_indices = np.argsort(distances)[:3]

d1 = distances[nearest_indices[0]]
d2 = distances[nearest_indices[1]]
d3 = distances[nearest_indices[2]]

dfs = []

# Loop through nearest weather stations and get climate normals
for idx in nearest_indices:
    # Get station ID and name
    station_id = station_data.loc[idx, 'id']
    station_name = station_data.loc[idx, 'name']
    
    # Make request to NOAA website for climate normals
    time.sleep(0.5)
    url = f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=normals-monthly-1991-2020&stations={station_id}&startDate=2022-01-01&endDate=2022-12-31&format=json"
    response = requests.get(url)
    
    # Parse JSON data
    json_data = response.json()
    
    # Extract climate normals for temperature and precipitation
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
    
    # turn into np arrays and adjust for elevation
    elev = station_data.loc[idx, 'elev']
    arr_max_temp_normals = np.array(max_temp_normals).astype(np.float64) + (((elev - input_elev)/1000)*lapse) # adjust to the elevation of the input coordinates
    arr_min_temp_normals = np.array(min_temp_normals).astype(np.float64) + (((elev - input_elev)/1000)*lapse) # same as above
    arr_precip_normals = np.array(precip_normals).astype(np.float64)
    arr_max_temp_std = np.array(max_temp_std).astype(np.float64)
    arr_min_temp_std = np.array(min_temp_std).astype(np.float64)

    # Compile/append results
    df = pd.DataFrame(data=np.array([arr_max_temp_normals, arr_min_temp_normals, arr_precip_normals, arr_max_temp_std, arr_min_temp_std]).astype(np.float64), index=['Monthly Mean Max Temp (F)', 'Monthly Mean Min Temp (F)', 'Precip (in)', 'Monthly Max Temp StdDev (F)', 'Monthly Min Temp StdDev (F)'], columns=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    dfs.append(df)

result = calculator.normals(d1, d2, d3, dfs, input_elev, lapse)

print(51*'- ')
print(f'Triangulum v{version} (stations supported = {station_data.shape[0]})')
print(51*'- ')
print(f'Estimated {normal_period} Climate Normals for {input_coords} (elev {round(input_elev)} ft)')
print(result)
print("")
print(f'Estimated {normal_period} Climate Normal Percentiles for {input_coords} (elev {round(input_elev)} ft)')
print(calculator.normal_probabilities(result))
print("")
print(f'Estimated {normal_period} Climate Normal Occurrence Probabilities for {input_coords} (elev {round(input_elev)} ft)')
print(calculator.occurrence_probabilities(result))
print("")
print(f'Predicted Climate Classification of {input_coords} (elev {round(input_elev)} ft)')
print(f'Koppen: {koppen.koppen(result)}')
print(f'Trewartha: {trewartha.trewartha(result)}')
print("")
print('Station Contributions:')
print(f'1. {station_data.loc[nearest_indices[0], "name"]} ({station_data.loc[nearest_indices[0], "id"]}): {round(100*(((1 - (d1/(d1 + d2 + d3)))/2)), 1)}%')
print(f'2. {station_data.loc[nearest_indices[1], "name"]} ({station_data.loc[nearest_indices[1], "id"]}): {round(100*(((1 - (d2/(d1 + d2 + d3)))/2)), 1)}%')
print(f'3. {station_data.loc[nearest_indices[2], "name"]} ({station_data.loc[nearest_indices[2], "id"]}): {round(100*(((1 - (d3/(d1 + d2 + d3)))/2)), 1)}%')
print(51*'- ')