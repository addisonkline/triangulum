import numpy as np
import pandas as pd
import requests
import calculator
#from geopy import distance
from bs4 import BeautifulSoup

# Input coordinates
#(38.45, -90.0060)
input_coords = (40.7128, -74.0060)

# Load weather station data
station_data = pd.read_json("weather_stations.json")

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
    url = f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=normals-monthly-1991-2020&stations={station_id}&startDate=2022-01-01&endDate=2022-12-31&format=json"
    response = requests.get(url)
    
    # Parse JSON data
    json_data = response.json()
    
    # Extract climate normals for temperature and precipitation
    max_temp_normals = []
    min_temp_normals = []
    precip_normals = []

    for month in range (12):
        max_temp_normals.append(json_data[month]['MLY-TMAX-NORMAL'])
        min_temp_normals.append(json_data[month]['MLY-TMIN-NORMAL'])
        precip_normals.append(json_data[month]['MLY-PRCP-NORMAL'])
    
    # Print results
    df = pd.DataFrame(data=np.array([max_temp_normals, min_temp_normals, precip_normals]).astype(np.float64), index=['Max Temp (F)', 'Min Temp (F)', 'Precip (in)'], columns=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    #print(f'Station Name: {station_name}, Distance: {distances[idx]} units')
    #print(df)
    dfs.append(df)

print(f'Estimated Climate Normals for {input_coords}')
print(calculator.calculate(d1, d2, d3, dfs))
print("")
print('Station Contributions:')
print(f'1. {station_data.loc[nearest_indices[0], "name"]} ({station_data.loc[nearest_indices[0], "id"]}): {round(100*(((1 - (d1/(d1 + d2 + d3)))/2)), 1)}%')
print(f'2. {station_data.loc[nearest_indices[1], "name"]} ({station_data.loc[nearest_indices[1], "id"]}): {round(100*(((1 - (d2/(d1 + d2 + d3)))/2)), 1)}%')
print(f'3. {station_data.loc[nearest_indices[2], "name"]} ({station_data.loc[nearest_indices[2], "id"]}): {round(100*(((1 - (d3/(d1 + d2 + d3)))/2)), 1)}%')