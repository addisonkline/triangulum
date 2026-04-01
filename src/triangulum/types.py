from pydantic import BaseModel

from triangulum.consts import MONTH_STRS
from triangulum.utils import fill_string


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

    def pretty(
        self,
        column_width: int = 8,
        column_width_stations: int = 16,
    ) -> str:
        num_columns = 14 # 1 per month + annual + header
        len_line = ((2 + column_width) * num_columns) + 1

        final_str = "|" + ((len_line - 2) * "=") + "|"
        # Month row
        final_str += "\n| " + fill_string("month", column_width) + "| "
        final_str += "| ".join([fill_string(month, column_width) for month in MONTH_STRS])
        final_str += "| " + fill_string("annual", column_width) + "|"
        final_str += "\n|" + "|".join([fill_string("=", column_width + 1, "=") for i in range(num_columns)]) + "|"
        # T_max row
        final_str += "\n| " + fill_string("T_max", column_width) + "| "
        final_str += "| ".join([fill_string(str(self.temp_daily_max[int(month)]), column_width) for month in MONTH_STRS])
        final_str += "| " + fill_string("TODO", column_width) + "|"
        final_str += "\n|" + "|".join([fill_string("-", column_width + 1, "-") for i in range(num_columns)]) + "|"
        # T_avg row
        final_str += "\n| " + fill_string("T_avg", column_width) + "| "
        final_str += "| ".join([fill_string(str(self.temp_daily_mean[int(month)]), column_width) for month in MONTH_STRS])
        final_str += "| " + fill_string("TODO", column_width) + "|"
        final_str += "\n|" + "|".join([fill_string("-", column_width + 1, "-") for i in range(num_columns)]) + "|"
        # T_min row
        final_str += "\n| " + fill_string("T_min", column_width) + "| "
        final_str += "| ".join([fill_string(str(self.temp_daily_min[int(month)]), column_width) for month in MONTH_STRS])
        final_str += "| " + fill_string("TODO", column_width) + "|"
        final_str += "\n|" + "|".join([fill_string("-", column_width + 1, "-") for i in range(num_columns)]) + "|"
        # P_avg row
        final_str += "\n| " + fill_string("P_avg", column_width) + "| "
        final_str += "| ".join([fill_string(str(self.precip_monthly_mean[int(month)]), column_width) for month in MONTH_STRS])
        final_str += "| " + fill_string("TODO", column_width) + "|"

        final_str += "\n|" + ((len_line - 2) * "=") + "|"

        # station info section
        num_columns_stations = 6
        len_line_stations = ((2 + column_width_stations) * num_columns_stations) + 1
        final_str += "\n| " + fill_string("station", column_width_stations) + "| "
        final_str += fill_string("name", column_width_stations) + "| "
        final_str += fill_string("lat", column_width_stations) + "| "
        final_str += fill_string("lon", column_width_stations) + "| "
        final_str += fill_string("dist", column_width_stations) + "| "
        final_str += fill_string("weight", column_width_stations) + "| "
        final_str += "\n|" + "|".join([fill_string("=", column_width_stations + 1, "=") for i in range(num_columns_stations)]) + "|"
        for station_id, station_info in self.stations.items():
            final_str += "\n| " + fill_string(station_id, column_width_stations) + "| "
            final_str += fill_string(station_info.name, column_width_stations) + "| "
            final_str += fill_string(str(station_info.lat), column_width_stations) + "| "
            final_str += fill_string(str(station_info.lon), column_width_stations) + "| "
            final_str += fill_string(str(station_info.distance), column_width_stations) + "| "
            final_str += fill_string(str(station_info.weight), column_width_stations) + "| "
            final_str += "\n|" + "|".join([fill_string("-", column_width_stations + 1, "-") for i in range(num_columns_stations)]) + "|"

        final_str += "\n|" + ((len_line_stations - 2) * "=") + "|"

        return final_str
