"""
triangulum/models/responses.py
Created by Addison Kline in December 2024
"""
# external imports
from pydantic import BaseModel
from pandas import DataFrame
# internal imports
from triangulum.models.station import Station

class NormalsResponse(BaseModel):
    # input values
    lat: float
    lon: float
    metric: bool
    # output values
    # metadata
    elev: float
    timestamp: str
    # actual normals
    normals: DataFrame

    class Config:
        arbitrary_types_allowed=True

class NormalProbabilityResponse(BaseModel):
    # input values
    lat: float
    lon: float
    metric: bool
    # output values
    # metadata
    elev: float
    timestamp: str
    # actual normal probs
    normal_probs: DataFrame

    class Config:
        arbitrary_types_allowed=True

class OccurrenceProbabilityResponse(BaseModel):
    # input values
    lat: float
    lon: float
    metric: bool
    # output values
    # metadata
    elev: float
    timestamp: str
    # actual normal probs
    occurrence_probs: DataFrame

    class Config:
        arbitrary_types_allowed=True

class KoppenResponse(BaseModel):
    # input values
    lat: float
    lon: float
    metric: bool
    # output values
    # metadata
    elev: float
    timestamp: str
    # actual classification stuff
    code: str
    summary: str

    class Config:
        arbitrary_types_allowed=True

class TrewarthaResponse(BaseModel):
    # input values
    lat: float
    lon: float
    metric: bool
    # output values
    # metadata
    elev: float
    timestamp: str
    # actual classification stuff
    code: str
    summary: str
    
    class Config:
        arbitrary_types_allowed=True

class SummaryResponse(BaseModel):
    # input values
    lat: float
    lon: float
    metric: bool
    # output values
    # metadata
    elev: float
    timestamp: str
    # dataframes
    normals: NormalsResponse
    normal_probs: DataFrame
    occurrence_probs: DataFrame
    # classification strings
    koppen: KoppenResponse
    trewartha: TrewarthaResponse
    # other
    nearest_stations: list[Station]
    
    class Config:
        arbitrary_types_allowed=True
