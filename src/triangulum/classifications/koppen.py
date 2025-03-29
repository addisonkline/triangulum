"""
triangulum/classifications/koppen.py
Created by Addison Kline in December 2024
"""
# external imports
import pandas as pd
import numpy as np
from enum import Enum
# internal imports

class Aridity(Enum):
    ARID = 1,
    SEMIARID = 2,
    HUMID = 3

def calculate_koppen(normals: pd.DataFrame) -> tuple[str, str]:
    """
    Given a DataFrame of metric normals, determine the Koppen classification associated with said normals.
    Specifically, return a tuple of two strings:
        1) the classification string itself (e.g. "Csa" or "Aw"), and 

        2) a short summary of the classification (e.g. "Temperate, dry summer, hot summer" and "Tropical, dry season", respectively).
    """
    code: str = ""
    summary: str = ""

    if is_tropical(normals):
        code += "A"
        summary += "Tropical, "

        if is_Af(normals):
            code += "f"
            summary += "no dry season"
        elif is_Am(normals):
            code += "m"
            summary += "monsoon"
        else: # is Aw
            code += "w"
            summary += "dry season"
    elif is_polar(normals):
        code += "E"
        summary += "Polar, "

        if is_EF(normals):
            code += "F"
            summary += "ice cap"
        else:
            code += "T"
            summary += "tundra"
    else: # neither tropical nor polar
        if get_aridity(normals) == Aridity.ARID:
            code += "BW"
            summary += "Desert, "

            if is_hot(normals):
                code += "h"
                summary += "hot"
            else:
                code += "k"
                summary += "cold"
        elif get_aridity(normals) == Aridity.SEMIARID:
            code += "BS"
            summary += "Semi-arid, "

            if is_hot(normals):
                code += "h"
                summary += "hot"
            else:
                code += "k"
                summary += "cold"
        else: # humid
            pass

    return (code, summary)

def is_tropical(normals: pd.DataFrame) -> bool:
    """
    A climate is considered tropical if the mean temp is >= 18 C in every month.
    """
    tmean = (normals['tmax'] + normals['tmin']) / 2
    return True if (np.mean(tmean >= 18) == 1) else False

def is_Af(normals: pd.DataFrame) -> bool:
    """
    A tropical climate is considered a tropical rainforest climate if all months have at least 60 mm of precip.
    """
    return True if (np.mean(normals['precip'] >= 60) == 1) else False

def is_Am(normals: pd.DataFrame) -> bool:
    """
    A tropical climate is considered a tropical monsoon climate if all months have otherwise at least 100 - (total annual precip / 25) mm of precip.
    """
    return True if (np.mean(normals['precip'] >= (100 - (normals['precip'].sum() / 25)))) else False

def is_polar(normals: pd.DataFrame) -> bool:
    """
    A climate is considered polar if the mean temp is below 10 C every month.
    """
    tmean = (normals['tmax'] + normals['tmin']) / 2
    return True if (np.mean(tmean < 10) == 1) else False

def is_EF(normals: pd.DataFrame) -> bool:
    """
    A polar climate is considered an ice cap climate if the mean temp is below 0 C every month.
    """
    tmean = (normals['tmax'] + normals['tmin']) / 2
    return True if (np.mean(tmean < 0) == 1) else False

def get_aridity(normals: pd.DataFrame) -> Aridity:
    """
    Determine whether a given climate is arid, semiarid, or neither (humid).
    """
    threshold = np.mean((normals['tmax'] + normals['tmin']) / 2) * 20
    if (normals['precip'][3:8].sum() / normals['precip'].sum()) >= 0.7:
        threshold += 240
    elif (normals['precip'][3:8].sum() / normals['precip'].sum()) >= 0.3:
        threshold += 140

    if (normals['precip'] / threshold) >= 1:
        return Aridity.HUMID
    elif (normals['precip'] / threshold) >= 0.5:
        return Aridity.SEMIARID
    else:
        return Aridity.HUMID

def is_hot(normals: pd.DataFrame) -> bool:
    """
    An arid or semi-arid climate is considered hot if the annual mean temperature is at least 18 C.
    """
    tmean_annual = np.mean((normals['tmax'] + normals['tmin']) / 2)
    return True if tmean_annual >= 18 else False

def is_temperate(normals: pd.DataFrame) -> bool:
    """
    A climate is temperate if it is neither tropical, polar, arid, nor semi-arid, and all months have a mean temp of at least -3 C.
    """
    tmean = (normals['tmax'] + normals['tmin']) / 2
    return True if (np.mean(tmean > -3) == 1) else False
