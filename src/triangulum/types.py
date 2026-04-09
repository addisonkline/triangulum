from calendar import month_abbr

from pydantic import BaseModel
from rich import box
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from triangulum.consts import MONTH_STRS
from triangulum.utils import fill_string, get_current_version

KM_TO_MI = 0.621371


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
            precip_monthly_mean={
                month.month: month.precip_monthly_mean for month in months
            },
        )


class ClimateNormalsEstimate(ClimateNormals):
    stations: dict[str, StationEstimateInfo]
    imperial: bool = False

    def pretty(
        self,
        column_width: int = 8,
        column_width_stations: int = 16,
    ) -> str:
        normal_rows = self._iter_normals_rows()
        metric_column_width = max(column_width, len("Daily mean"))
        month_labels = self._month_labels()
        widths = [metric_column_width] + [column_width] * (len(month_labels) + 1)

        lines = [
            "---",
            f"Triangulum v{get_current_version()}",
            f"Temperature: {self._temperature_unit()} | Precipitation: {self._precipitation_unit()}",
            "---",
            self._plain_separator(widths, "="),
            self._plain_row(["Metric", *month_labels, "Year"], widths),
            self._plain_separator(widths, "="),
        ]

        for idx, (label, values, kind) in enumerate(normal_rows):
            ordered_values = self._ordered_month_values(values)
            annual_value = self._annual_value(values, kind=kind)
            formatter = (
                self._format_temperature
                if kind == "temperature"
                else self._format_precipitation
            )
            lines.append(
                self._plain_row(
                    [
                        label,
                        *[formatter(value) for value in ordered_values],
                        formatter(annual_value),
                    ],
                    widths,
                )
            )

            if idx < len(normal_rows) - 1:
                lines.append(self._plain_separator(widths, "-"))

        lines.extend(
            [
                self._plain_separator(widths, "="),
                "",
                "Nearby Stations",
            ]
        )

        distance_header = self._distance_column_label()
        station_headers = ["Station", "Name", "Lat", "Lon", distance_header, "Weight"]
        station_widths = [
            max(column_width_stations, len("Station")),
            column_width_stations,
            max(9, len("Lat")),
            max(10, len("Lon")),
            max(10, len(distance_header)),
            max(8, len("Weight")),
        ]

        lines.append(self._plain_separator(station_widths, "="))
        lines.append(self._plain_row(station_headers, station_widths))
        lines.append(self._plain_separator(station_widths, "="))

        station_rows = self._sorted_station_items()
        for idx, (station_id, station_info) in enumerate(station_rows):
            lines.append(
                self._plain_row(
                    [
                        station_id,
                        station_info.name,
                        f"{station_info.lat:.3f}",
                        f"{station_info.lon:.3f}",
                        self._format_distance(station_info.distance),
                        self._format_weight(station_info.weight),
                    ],
                    station_widths,
                )
            )

            if idx < len(station_rows) - 1:
                lines.append(self._plain_separator(station_widths, "-"))

        lines.append(self._plain_separator(station_widths, "="))

        return "\n".join(lines)

    def rich_print(
        self,
        column_width: int = 8,
        column_width_stations: int = 16,
    ) -> None:
        _ = column_width, column_width_stations
        Console().print(self.render())

    def render(self) -> Group:
        header = Text.assemble(
            (f"Triangulum v{get_current_version()}", "bold"),
            (
                f"  Temperature: {self._temperature_unit()}  Precipitation: {self._precipitation_unit()}",
                "dim",
            ),
        )
        return Group(
            header,
            Text(),
            self._build_normals_table(),
            Text(),
            self._build_station_table(),
        )

    def _build_normals_table(self) -> Table:
        table = Table(
            title="Estimated Climate Normals",
            caption="Year = annual mean temperature / annual total precipitation",
            box=box.SIMPLE_HEAVY,
            header_style="bold",
            title_style="bold cyan",
            pad_edge=False,
            padding=(0, 0),
        )
        table.add_column("Metric", style="bold", no_wrap=True)

        for month_label in self._month_labels():
            table.add_column(month_label, justify="right", min_width=4, no_wrap=True)

        table.add_column("Year", justify="right", style="bold", no_wrap=True)

        for label, values, kind in self._iter_normals_rows():
            ordered_values = self._ordered_month_values(values)
            annual_value = self._annual_value(values, kind=kind)

            if kind == "temperature":
                row = [label]
                row.extend(
                    self._render_temperature_cell(value) for value in ordered_values
                )
                row.append(self._render_temperature_cell(annual_value, annual=True))
            else:
                row = [label]
                row.extend(
                    self._render_precipitation_cell(value) for value in ordered_values
                )
                row.append(self._render_precipitation_cell(annual_value, annual=True))

            table.add_row(*row)

        return table

    def _build_station_table(self) -> Table:
        distance_header = self._distance_column_label()
        table = Table(
            title="Nearby Station Contribution",
            caption=f"{distance_header} = great-circle distance from the input coordinates",
            box=box.SIMPLE_HEAVY,
            header_style="bold",
            title_style="bold cyan",
            pad_edge=False,
            padding=(0, 1),
        )
        table.add_column("Station", style="bold cyan", no_wrap=True)
        table.add_column("Name", overflow="fold", min_width=24)
        table.add_column("Lat", justify="right")
        table.add_column("Lon", justify="right")
        table.add_column(distance_header, justify="right")
        table.add_column("Weight", justify="right", style="bold green")

        for station_id, station_info in self._sorted_station_items():
            table.add_row(
                station_id,
                station_info.name,
                f"{station_info.lat:.3f}",
                f"{station_info.lon:.3f}",
                self._format_distance(station_info.distance),
                self._format_weight(station_info.weight),
            )

        return table

    def _iter_normals_rows(
        self,
    ) -> list[tuple[str, dict[int, float], str]]:
        return [
            ("Mean max", self.temp_daily_max, "temperature"),
            ("Daily mean", self.temp_daily_mean, "temperature"),
            ("Mean min", self.temp_daily_min, "temperature"),
            ("Precip", self.precip_monthly_mean, "precipitation"),
        ]

    def _sorted_station_items(self) -> list[tuple[str, StationEstimateInfo]]:
        return sorted(
            self.stations.items(),
            key=lambda item: item[1].weight,
            reverse=True,
        )

    def _ordered_month_keys(self) -> list[int]:
        return [int(month) for month in MONTH_STRS]

    def _month_labels(self) -> list[str]:
        return [month_abbr[month] for month in self._ordered_month_keys()]

    def _ordered_month_values(self, values: dict[int, float]) -> list[float]:
        return [
            self._month_value(values, month) for month in self._ordered_month_keys()
        ]

    def _month_value(self, values: dict[int, float], month: int) -> float:
        value = values.get(month)
        if value is not None:
            return float(value)

        month_str = f"{month:02d}"
        fallback_value = values.get(month_str)  # type: ignore[arg-type]
        if fallback_value is None:
            raise KeyError(f"missing monthly normal for month {month_str}")

        return float(fallback_value)

    def _annual_value(self, values: dict[int, float], kind: str) -> float:
        ordered_values = self._ordered_month_values(values)
        if kind == "precipitation":
            return sum(ordered_values)
        return sum(ordered_values) / len(ordered_values)

    def _temperature_unit(self) -> str:
        return "°F" if self.imperial else "°C"

    def _precipitation_unit(self) -> str:
        return "in" if self.imperial else "mm"

    def _format_temperature(self, value: float) -> str:
        return f"{value:.1f}"

    def _format_precipitation(self, value: float) -> str:
        precision = 2 if self.imperial else 0
        return f"{value:.{precision}f}"

    def _format_distance(self, value: float) -> str:
        display_value = value * KM_TO_MI if self.imperial else value
        return f"{display_value:.1f}"

    def _format_weight(self, value: float) -> str:
        return f"{value:.1%}"

    def _distance_unit(self) -> str:
        return "mi" if self.imperial else "km"

    def _distance_column_label(self) -> str:
        return f"Dist ({self._distance_unit()})"

    def _plain_row(self, cells: list[str], widths: list[int]) -> str:
        rendered_cells = [
            fill_string(cell, width) for cell, width in zip(cells, widths, strict=True)
        ]
        return "| " + " | ".join(rendered_cells) + " |"

    def _plain_separator(self, widths: list[int], char: str) -> str:
        return "|" + "|".join(char * (width + 2) for width in widths) + "|"

    def _render_temperature_cell(
        self,
        value: float,
        annual: bool = False,
    ) -> Text:
        style = self._temperature_style(value)
        if annual:
            style = f"bold {style}"
        return Text(self._format_temperature(value), style=style)

    def _render_precipitation_cell(
        self,
        value: float,
        annual: bool = False,
    ) -> Text:
        style = self._precipitation_style(value)
        if annual:
            style = f"bold {style}"
        return Text(self._format_precipitation(value), style=style)

    def _temperature_style(self, value: float) -> str:
        if self._is_below_freezing(value):
            return "bold bright_white on blue"

        if self.imperial:
            if value < 45.0:
                return "bright_cyan"
            if value < 55.0:
                return "cyan"
            if value < 65.0:
                return "bright_white"
            if value < 75.0:
                return "white"
            if value < 86.0:
                return "yellow"
            if value < 95.0:
                return "bright_red"
            return "red"

        if value < 7.0:
            return "bright_cyan"
        if value < 13.0:
            return "cyan"
        if value < 18.0:
            return "bright_white"
        if value < 24.0:
            return "white"
        if value < 30.0:
            return "yellow"
        if value < 35.0:
            return "bright_red"
        return "red"

    def _is_below_freezing(self, value: float) -> bool:
        freezing_point = 32.0 if self.imperial else 0.0
        return value < freezing_point

    def _precipitation_style(self, value: float) -> str:
        if self.imperial:
            if value < 1.0:
                return "bright_cyan"
            if value < 2.0:
                return "cyan"
            if value < 4.0:
                return "blue"
            if value < 6.0:
                return "bright_blue"
            return "bold bright_blue"

        if value < 25.0:
            return "bright_cyan"
        if value < 50.0:
            return "cyan"
        if value < 100.0:
            return "blue"
        if value < 150.0:
            return "bright_blue"
        return "bold bright_blue"
