"""
triangulum/cli.py
Created by Addison Kline in March 2025
"""
from typer import Typer
from triangulum.api import Triangulum

app = Typer()

@app.command()
def normals(lat: float, lon: float, metric: bool = False, normals: str = "1991-2020"):
    """
    Get the climate normals for a given set of coordinates.
    """
    client = Triangulum(metric, normals)
    response = client.get_location_normals(lat, lon)
    print(response.normals)

if __name__ == "__main__":
    app()