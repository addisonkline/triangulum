"""
triangulum/models/station.py
Created by Addison Kline in December 2024
"""
# external imports
from pydantic import BaseModel
# internal imports

class Station(BaseModel):
    id: str
    lat: float
    lon: float
    elev: float
    city: str
    state: str
    country: str
    # info relating to given loc
    distance_from_loc: float