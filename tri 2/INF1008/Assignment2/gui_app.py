"""
Flask GUI for Fire Emergency Response Optimisation System

Provides a web interface with a clickable map:
- Click anywhere on the San Francisco map to set an emergency ("Start Fire")
- Optionally choose a specific fire station, or let the system pick the best one
- See the optimized route drawn on the map
"""

from flask import Flask, render_template, request, jsonify
from fire_response_optimizer import FireResponseOptimizer


DATA_PATH = "data/fire_dept.csv"  # adjust if your CSV name is different


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

        # Compute route and Dijkstra trace
        if station_id:
            path, distance, visit_order = optimizer.find_optimal_route_with_trace(
                (lat, lon), station_id
            )
        else:
            # Auto-select nearest station, then get trace for that route
            selected_station, _, _ = optimizer.find_nearest_fire_station((lat, lon))
            station_id = selected_station
            path, distance, visit_order = optimizer.find_optimal_route_with_trace(
                (lat, lon), station_id
            )

        coords_map = optimizer.graph_builder.get_node_coordinates()
        path_coords = [
            {"lat": coords_map[node][0], "lon": coords_map[node][1]}
            for node in path
            if node in coords_map
        ]

        return jsonify(
            {
                "station_id": station_id,
                "distance_km": distance,
                "path": path,
                "path_coords": path_coords,
                "visit_order": visit_order,
            }
        )

    return app


if __name__ == "__main__":
    app = create_app()
    # Debug mode for development; visit http://127.0.0.1:5000
    app.run(debug=True)

