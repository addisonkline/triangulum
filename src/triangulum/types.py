from pydantic import BaseModel


class StationInfo(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    elev: float


class StationEstimateInfo(StationInfo):
    distance: float
    weight: float


class ClimateNormalMonth(BaseModel):
    month: int
    temp_daily_mean: float
    temp_daily_max: float
    temp_daily_min: float
    precip_monthly_mean: float


class ClimateNormals(BaseModel):
    temp_daily_mean: dict[int, float]
    temp_daily_max: dict[int, float]
    temp_daily_min: dict[int, float]
    precip_monthly_mean: dict[int, float]

    @staticmethod
    def from_monthly(months: list[ClimateNormalMonth]) -> "ClimateNormals":
        return ClimateNormals(
            temp_daily_max={month.month: month.temp_daily_max for month in months},
            temp_daily_mean={month.month: month.temp_daily_mean for month in months},
            temp_daily_min={month.month: month.temp_daily_min for month in months},
            precip_monthly_mean={month.month: month.precip_monthly_mean for month in months}
        )


class ClimateNormalsEstimate(ClimateNormals):
    stations: dict[str, StationEstimateInfo]
