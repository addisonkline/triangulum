# Triangulum: A climate estimation project for the continental United States
## General Information
- Project creator: Addison Kline (www.github.com/addisonkline)
- Project started: March 26, 2023
- Current version: 1.0
- Current number of stations supported: 54

## Summary
The name Triangulum (Latin for "triangle") comes from the method of triangulation used to estimate climate normals. The program takes in a set of input coordinates and finds the three nearest weather stations with 1991-2020 climate normal data for temperature and precipitation. It then calculates a weighted average accordingly (shorter distance = heavier weight) and finally adjusts for elevation. 

Currently, only a small portion of the 6306 qualifying weather stations in the United States are supported, though this will soon change. In the future, I also plan on adding climate classification functionality that takes the estimated normals and estimates calculates the corresponding Koppen and Trewartha classifications. I also plan on adding more nuance to the lapse rate functionality used to adjust for elevation.

## Attribution
All climate and weather station data comes from the National Centers for Environmental Information (NCEI) U.S. climate normal database (www.ncei.noaa.gov/access/search/data-search/normals-monthly-1991-2020). Input point elevation data is courtesy of the United States Geological Survey (USGS) National Map Elevation Point Query Service (apps.nationalmap.gov/epqs/).
