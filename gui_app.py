"""
Flask GUI for Fire Emergency Response Optimisation System

Provides a web interface with a clickable map:
- Click anywhere on the San Francisco map to set an emergency ("Start Fire")
- Optionally choose a specific fire station, or let the system pick the best one
- See the optimized route drawn on the map (follows actual streets via OSRM)
"""

from typing import List, Tuple, Optional

import requests
from flask import Flask, render_template, request, jsonify
from fire_response_optimizer import FireResponseOptimizer


DATA_PATH = "data/fire_dept.csv"  # adjust if your CSV name is different

OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"


def get_street_route(start: Tuple[float, float], end: Tuple[float, float]) -> Optional[List[dict]]:
    """
    Fetch road-following route from OSRM (Open Source Routing Machine).
    Returns list of {lat, lon} dicts, or None if the request fails.
    """
    # OSRM expects lon,lat order
    coords_str = f"{start[1]},{start[0]};{end[1]},{end[0]}"
    url = f"{OSRM_BASE}/{coords_str}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None
        # GeoJSON coordinates are [lon, lat]
        coords = data["routes"][0]["geometry"]["coordinates"]
        return [{"lat": lat, "lon": lon} for lon, lat in coords]
    except Exception:
        return None


def create_app() -> Flask:
    app = Flask(__name__)

    # Initialize optimizer once, reused across requests
    optimizer = FireResponseOptimizer(
        data_path=DATA_PATH,
        graph_type="proximity",
        max_distance_km=5.0,
    )
    optimizer.initialize()

    @app.route("/")
    def index():
        # Pass fire station coordinates to the frontend
        stations = [
            {"id": sid, "lat": coords[0], "lon": coords[1]}
            for sid, coords in optimizer.fire_stations.items()
        ]
        return render_template("index.html", stations=stations)

    @app.route("/route", methods=["POST"])
    def route():
        data = request.get_json(force=True)
        lat = float(data["lat"])
        lon = float(data["lon"])
        station_id = data.get("station_id") or None

        if station_id == "auto":
            station_id = None

        # Assignment requirement: compare nearest station by
        # straight-line distance vs nearest by Dijkstra shortest path.
        straight_station_id, straight_distance = optimizer.find_nearest_fire_station_straight_line((lat, lon))

        # Compute route using existing optimizer methods
        try:
            if station_id:
                path, distance = optimizer.find_optimal_route((lat, lon), station_id)
            else:
                station_id, distance, path = optimizer.find_nearest_fire_station((lat, lon))
        except Exception as e:
            # Surface a clear error instead of a 500 so the frontend
            # can show a friendly message when no route is possible.
            return jsonify({"error": str(e)}), 400

        coords_map = optimizer.graph_builder.get_node_coordinates()
        path_coords = [
            {"lat": coords_map[node][0], "lon": coords_map[node][1]}
            for node in path
            if node in coords_map
        ]

        used_osrm = False

        # Fetch street-following route from OSRM for display (start -> end)
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


if __name__ == "__main__":
    app = create_app()
    # Debug mode for development; visit http://127.0.0.1:5000
    app.run(debug=True)

