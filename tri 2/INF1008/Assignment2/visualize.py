"""
Visualization module for Fire Emergency Response Optimisation System

Creates visualizations of routes found by Dijkstra's algorithm.
"""

import folium
from typing import List, Tuple, Dict
from fire_response_optimizer import FireResponseOptimizer


def visualize_route(optimizer: FireResponseOptimizer, 
                   emergency_location: Tuple[float, float],
                   fire_station_id: str = None,
                   output_file: str = "route_map.html"):
    """
    Visualize the optimal route on an interactive map.
    
    Args:
        optimizer: FireResponseOptimizer instance
        emergency_location: (lat, lon) of emergency
        fire_station_id: Optional specific fire station
        output_file: Output HTML file path
    """
    # Find optimal route
    if fire_station_id:
        path, distance = optimizer.find_optimal_route(emergency_location, fire_station_id)
        station_id = fire_station_id
    else:
        station_id, distance, path = optimizer.find_nearest_fire_station(emergency_location)
    
    # Get coordinates for all nodes in path
    coords = optimizer.graph_builder.get_node_coordinates()
    path_coords = [coords[node] for node in path if node in coords]
    
    if not path_coords:
        print("No path found to visualize")
        return
    
    # Create map centered on emergency location
    m = folium.Map(location=emergency_location, zoom_start=13)
    
    # Add fire station marker
    station_coords = optimizer.fire_stations[station_id]
    folium.Marker(
        station_coords,
        popup=f"Fire Station: {station_id}",
        icon=folium.Icon(color='red', icon='fire', prefix='fa')
    ).add_to(m)
    
    # Add emergency location marker
    folium.Marker(
        emergency_location,
        popup=f"Emergency Location<br>Distance: {distance:.2f} km",
        icon=folium.Icon(color='orange', icon='exclamation-triangle', prefix='fa')
    ).add_to(m)
    
    # Draw route path
    if len(path_coords) > 1:
        folium.PolyLine(
            path_coords,
            color='blue',
            weight=4,
            opacity=0.7,
            popup=f"Optimal Route: {distance:.2f} km"
        ).add_to(m)
    
    # Add all fire stations
    for sid, coords in optimizer.fire_stations.items():
        if sid != station_id:
            folium.Marker(
                coords,
                popup=f"Fire Station: {sid}",
                icon=folium.Icon(color='lightgray', icon='fire', prefix='fa')
            ).add_to(m)
    
    # Save map
    m.save(output_file)
    print(f"Map saved to {output_file}")
    print(f"Open {output_file} in your browser to view the route")


def visualize_multiple_routes(optimizer: FireResponseOptimizer,
                             emergency_locations: List[Tuple[float, float]],
                             output_file: str = "multiple_routes_map.html"):
    """
    Visualize multiple emergency routes on a single map.
    
    Args:
        optimizer: FireResponseOptimizer instance
        emergency_locations: List of (lat, lon) tuples
        output_file: Output HTML file path
    """
    # Calculate center of all locations
    all_lats = [loc[0] for loc in emergency_locations]
    all_lons = [loc[1] for loc in emergency_locations]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    m = folium.Map(location=(center_lat, center_lon), zoom_start=12)
    
    # Colors for different routes
    colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'lightred']
    
    # Process each emergency
    results = optimizer.optimize_multiple_emergencies(emergency_locations)
    
    for i, (emergency_id, result) in enumerate(results.items()):
        if 'error' in result:
            continue
        
        color = colors[i % len(colors)]
        station_id = result['assigned_station']
        path = result['path']
        
        # Get coordinates
        coords = optimizer.graph_builder.get_node_coordinates()
        path_coords = [coords[node] for node in path if node in coords]
        
        # Add emergency marker
        folium.Marker(
            result['location'],
            popup=f"{emergency_id}<br>Station: {station_id}<br>Distance: {result['distance_km']:.2f} km",
            icon=folium.Icon(color='orange', icon='exclamation-triangle', prefix='fa')
        ).add_to(m)
        
        # Add route
        if len(path_coords) > 1:
            folium.PolyLine(
                path_coords,
                color=color,
                weight=3,
                opacity=0.6,
                popup=f"{emergency_id} Route"
            ).add_to(m)
    
    # Add all fire stations
    for sid, station_coords in optimizer.fire_stations.items():
        folium.Marker(
            station_coords,
            popup=f"Fire Station: {sid}",
            icon=folium.Icon(color='red', icon='fire', prefix='fa')
        ).add_to(m)
    
    m.save(output_file)
    print(f"Map saved to {output_file}")


if __name__ == "__main__":
    # Example usage
    from fire_response_optimizer import FireResponseOptimizer
    
    optimizer = FireResponseOptimizer(
        data_path="data/fire_department_calls.csv",
        graph_type='proximity'
    )
    
    try:
        optimizer.initialize()
        
        # Visualize single route
        emergency = (37.7749, -122.4194)
        visualize_route(optimizer, emergency)
        
        # Visualize multiple routes
        emergencies = [
            (37.7849, -122.4094),
            (37.7649, -122.4294),
            (37.7549, -122.4394),
        ]
        visualize_multiple_routes(optimizer, emergencies)
        
    except Exception as e:
        print(f"Error: {e}")
