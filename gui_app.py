"""
Flask web GUI for fire emergency routing.

Flow:
1. FireResponseOptimizer loads the CSV, builds a proximity graph (stations + sample incidents),
   and uses Dijkstra for shortest paths on that graph.
2. GET / serves a Leaflet map; the user picks an emergency and optional station.
3. POST /route receives lat/lon (and optional station). The backend runs Dijkstra (or a fixed
   station), compares straight-line nearest vs graph-based nearest, and returns path + distances.
4. The map polyline is first built from graph node coordinates; if OSRM responds, it is replaced
   with a road-following geometry for display only (routing decision stays Dijkstra on the graph).
"""

import os
import threading
import time
import webbrowser
from typing import List, Tuple, Optional

import requests
from flask import Flask, render_template, request, jsonify
from fire_response_optimizer import FireResponseOptimizer

# Prefer data/ inside the repo; fall back to ../data/ (e.g. CSV next to the cloned folder).
_DATA_CANDIDATES = ["data/fire_dept.csv", "../data/fire_dept.csv"]
DATA_PATH = next(
    (p for p in _DATA_CANDIDATES if os.path.exists(p)),
    "data/fire_dept.csv"
)

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"


def get_street_route(start: Tuple[float, float], end: Tuple[float, float]) -> Optional[List[dict]]:
    """
    Fetch road-following route from OSRM (Open Source Routing Machine).
    Returns list of {lat, lon} dicts, or None if the request fails.
    """
    coords_str = f"{start[1]},{start[0]};{end[1]},{end[0]}"
    url = f"{OSRM_BASE}/{coords_str}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        coords = data["routes"][0]["geometry"]["coordinates"]
        return [{"lat": lat, "lon": lon} for lon, lat in coords]
    except Exception:
        return None


def create_app() -> Flask:
    app = Flask(__name__)
    # One optimizer for the process: load data once, build graph once, reuse for every /route call.
    optimizer = FireResponseOptimizer(
        data_path=DATA_PATH,
        graph_type="proximity",
        max_distance_km=5.0,
    )
    optimizer.initialize()

    @app.route("/")
    def index():
        stations = [
            {"id": sid, "lat": coords[0], "lon": coords[1]}
            for sid, coords in optimizer.fire_stations.items()
        ]
        return render_template("index.html", stations=stations)

    @app.route("/route", methods=["POST"])
    def route():
        # Body: { "lat", "lon", "station_id": optional | "auto" }.
        data = request.get_json(force=True)
        lat = float(data["lat"])
        lon = float(data["lon"])
        station_id = data.get("station_id") or None

        if station_id == "auto":
            station_id = None

        # Straight-line nearest (geodesic) vs Dijkstra on the graph — can differ when the graph is not uniform.
        straight_station_id, straight_distance = optimizer.find_nearest_fire_station_straight_line((lat, lon))

        try:
            if station_id:
                path, distance = optimizer.find_optimal_route((lat, lon), station_id)
            else:
                # Auto: Dijkstra from all stations to this emergency (nearest on the graph).
                station_id, distance, path = optimizer.find_nearest_fire_station((lat, lon))
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        coords_map = optimizer.graph_builder.get_node_coordinates()
        path_coords = [
            {"lat": coords_map[node][0], "lon": coords_map[node][1]}
            for node in path
            if node in coords_map
        ]

        used_osrm = False
        #  replace start→end segment with OSRM driving geometry for the map only.
        if len(path_coords) >= 2:
            start = (path_coords[0]["lat"], path_coords[0]["lon"])
            end = (path_coords[-1]["lat"], path_coords[-1]["lon"])
            street_coords = get_street_route(start, end)
            if street_coords:
                path_coords = street_coords
                used_osrm = True

        return jsonify(
            {
                "station_id": station_id,
                "distance_km": distance,
                "path": path,
                "path_coords": path_coords,
                "straight_station_id": straight_station_id,
                "straight_distance_km": straight_distance,
                "used_osrm": used_osrm,
            }
        )

    return app


def _open_browser_when_ready(url: str = "http://127.0.0.1:5000", delay_sec: float = 1.25) -> None:
    """Open default browser after a short delay so the server is listening."""
    time.sleep(delay_sec)
    webbrowser.open(url)


if __name__ == "__main__":
    app = create_app()
    RUN_DEBUG = True
    # With debug reloader, only the worker has WERKZEUG_RUN_MAIN=true
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not RUN_DEBUG:
        threading.Thread(
            target=_open_browser_when_ready,
            kwargs={"url": "http://127.0.0.1:5000", "delay_sec": 1.25},
            daemon=True,
        ).start()
    app.run(debug=RUN_DEBUG)

