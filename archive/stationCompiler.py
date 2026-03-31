import requests
from pypdf import PdfReader

token = 'zEiJrayApRaCovHXbbezMyoBibhTilBL'

# Make request to NCEI API for list of weather stations with 1991-2020 normal data
url = "https://www.ncei.noaa.gov/access/search/data-search/normals-monthly-1991-2020?dataTypes=MLY-TMIN-NORMAL&dataTypes=MLY-TMAX-NORMAL&dataTypes=MLY-DUTR-NORMAL&dataTypes=MLY-PRCP-NORMAL&bbox=71.351,-178.217,18.925,179.769&place=Country:117"
response = requests.get(url, headers = {'token': token})

# testing pypdf
testUrl = 'https://www.ncei.noaa.gov/access/services/data/v1?dataset=normals-monthly-1991-2020&startDate=0001-01-01&endDate=9996-12-31&stations=USC00010063&format=pdf'
reader = PdfReader(testUrl)
text = reader.pages[0].extract_text()
print(text)
                        
# Parse JSON data
json_data = response.json()
print(json_data[0])
stations_data = json_data[0]['stations']

# Loop through stations and extract information
for station in stations_data:
    # Extract station information
    station_id = station['id']
    station_name = station['name']
    latitude = station['latitude']
    longitude = station['longitude']
    elevation = station['elevation']
    
    # Print results
    print(f"Station Name: {station_name}")
    print(f"Station ID: {station_id}")
    print(f"Latitude: {latitude}")
    print(f"Longitude: {longitude}")
    print(f"Elevation: {elevation}")
    print("")
