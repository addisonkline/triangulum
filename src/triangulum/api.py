"""
triangulum/api.py
Created by Addison Kline in December 2024
"""
# external imports
import datetime
# internal imports
from triangulum.models import *
from triangulum.utils import *

class Triangulum:
    """
    Class for the Triangulum API.
    """
    metric: bool
    normals_period: str

    def __init__(self, metric: bool, normals_period: str):
        """
        Constructor for the Triangulum class.
        """
        self.metric = metric

        self._validate_normals_period(normals_period)
        self.normals_period = normals_period
    
    def get_location_summary(self, lat: float, lon: float) -> SummaryResponse:
        """
        Concatenates all response objects returned below into a single summary.
        """
        self._validate_input_coords(lat, lon)

    def get_location_normals(self, lat: float, lon: float) -> NormalsResponse:
        """
        Given a set of coordinates, validate said coordinates and return a `NormalsResponse`.
        """
        self._validate_input_coords(lat, lon)

        elev = get_location_elev(self.metric, lat, lon)
        normals = get_location_normals(lat, lon)

        return NormalsResponse(
            lat=lat,
            lon=lon,
            metric=self.metric,
            elev=elev,
            timestamp=datetime.datetime.now(),
            normals=normals
        )

    def get_location_normal_probs(self, lat: float, lon: float) -> NormalProbabilityResponse:
        """
        Given a set of coordinates, validate said coordinates and return a `NormalProbabilityResponse`.
        """
        self._validate_input_coords(lat, lon)

        elev = get_location_elev(self.metric, lat, lon)
        normal_probs = get_location_normal_probs(lat, lon)

        return NormalProbabilityResponse(
            lat=lat,
            lon=lon,
            metric=self.metric,
            elev=elev,
            timestamp=datetime.datetime.now(),
            normal_probs=normal_probs
        )

    def get_location_occurrence_probs(self, lat: float, lon: float) -> OccurrenceProbabilityResponse:
        """
        Given a set of coordinates, validate said coordinates and return an `OccurrenceProbabilityResponse`.
        """
        self._validate_input_coords(lat, lon)

        elev = get_location_elev(lat, lon)
        occurrence_probs = get_location_occurrence_probs(self.metric, lat, lon)

        return OccurrenceProbabilityResponse(
            lat=lat,
            lon=lon,
            metric=self.metric,
            elev=elev,
            timestamp=datetime.datetime.now(),
            occurrence_probs=occurrence_probs
        )

    def get_location_koppen(self, lat: float, lon: float) -> KoppenResponse:
        """
        
        """
        self._validate_input_coords(lat, lon)

        raise NotImplementedError("koppen classification has not yet been implemented")

    def get_location_trewartha(self, lat: float, lon: float) -> TrewarthaResponse:
        """
        
        """
        self._validate_input_coords(lat, lon)

        raise NotImplementedError("trewartha classification has not yet been implemented")
    
    def get_nearest_stations(self, lat: float, lon: float) -> list[Station]:
        """
        Given a set of coordinates, validate said coordinates and return the 3 closest stations.
        """
        self._validate_input_coords(lat, lon)

        return get_location_nearest_stations(lat, lon)

    # private class methods
    def _validate_normals_period(self, normals_period: str):
        """
        Ensure the normals period given is valid.
        As of v2.0, only "1991-2020" is supported.
        """
        if not normals_period == "1991-2020":
            raise ValueError("invalid normals period given. only '1991-2020' is currently supported")
    
    def _validate_input_coords(self, lat: float, lon: float):
        """
        Ensure the given coordinates fall within the continental U.S.
        """
        if lat > 50.0 or lat < 20.0:
            raise ValueError("the given latitude must be within the continental U.S.")
        if lon > -66.0 or lon < -125.0:
            raise ValueError("the given longitude must be within the continental U.S.")