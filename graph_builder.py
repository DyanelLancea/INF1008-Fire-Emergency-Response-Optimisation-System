"""
Graph Builder for Fire Emergency Response System

This module builds a graph representation of locations (fire stations and emergencies)
for use with Dijkstra's algorithm.
"""

from typing import Dict, List, Tuple
from geopy.distance import geodesic
import math


class GraphBuilder:
    """
    Builds a weighted graph from fire stations and emergency locations.
    """
    
    def __init__(self):
        """Initialize the graph builder."""
        self.graph: Dict[str, Dict[str, float]] = {}
        self.node_coordinates: Dict[str, Tuple[float, float]] = {}
    
    def add_node(self, node_id: str, coordinates: Tuple[float, float]):
        """
        Add a node to the graph.
        
        Args:
            node_id: Unique identifier for the node
            coordinates: (latitude, longitude) tuple
        """
        if node_id not in self.graph:
            self.graph[node_id] = {}
        self.node_coordinates[node_id] = coordinates
    
    def add_edge(self, from_node: str, to_node: str, weight: float):
        """
        Add a directed edge to the graph.
        
        Args:
            from_node: Source node ID
            to_node: Target node ID
            weight: Edge weight (distance or time)
        """
        if from_node not in self.graph:
            self.graph[from_node] = {}
        self.graph[from_node][to_node] = weight
    
    def calculate_distance(self, coord1: Tuple[float, float], 
                          coord2: Tuple[float, float]) -> float:
        """
        Calculate distance between two coordinates in kilometers.
        
        Args:
            coord1: (lat, lon) tuple
            coord2: (lat, lon) tuple
        
        Returns:
            Distance in kilometers
        """
        return geodesic(coord1, coord2).kilometers
    
    def build_fully_connected_graph(self, locations: List[Tuple[float, float, str]]):
        """
        Build a fully connected graph from a list of locations.
        
        This creates edges between all pairs of nodes, which is useful
        for small networks but may be inefficient for large ones.
        
        Args:
            locations: List of (lat, lon, node_id) tuples
        """
        # Add all nodes
        for lat, lon, node_id in locations:
            self.add_node(node_id, (lat, lon))
        
        # Create edges between all pairs
        for i, (lat1, lon1, node1) in enumerate(locations):
            for j, (lat2, lon2, node2) in enumerate(locations):
                if i != j:
                    distance = self.calculate_distance((lat1, lon1), (lat2, lon2))
                    # Add bidirectional edges
                    self.add_edge(node1, node2, distance)
                    self.add_edge(node2, node1, distance)
    
    def build_proximity_graph(self, locations: List[Tuple[float, float, str]], 
                             max_distance_km: float = 5.0):
        """
        Build a graph where nodes are connected only if they're within max_distance_km.
        
        This creates a more realistic road network representation.
        
        Args:
            locations: List of (lat, lon, node_id) tuples
            max_distance_km: Maximum distance for edge creation
        """
        # Add all nodes
        for lat, lon, node_id in locations:
            self.add_node(node_id, (lat, lon))
        
        # Create edges only for nearby nodes
        for i, (lat1, lon1, node1) in enumerate(locations):
            for j, (lat2, lon2, node2) in enumerate(locations):
                if i != j:
                    distance = self.calculate_distance((lat1, lon1), (lat2, lon2))
                    if distance <= max_distance_km:
                        # Add bidirectional edges
                        self.add_edge(node1, node2, distance)
                        self.add_edge(node2, node1, distance)
    
    def build_grid_graph(self, fire_stations: Dict[str, Tuple[float, float]],
                        emergency_locations: List[Tuple[float, float, str]],
                        grid_size: int = 20):
        """
        Build a grid-based graph for more realistic road network simulation.
        
        Creates a grid of nodes and connects them in a grid pattern,
        then connects fire stations and emergencies to nearest grid nodes.
        
        Args:
            fire_stations: Dict mapping station_id to (lat, lon)
            emergency_locations: List of (lat, lon, call_id) tuples
            grid_size: Number of grid points per dimension
        """
        # Find bounding box
        all_lats = [coord[0] for coord in fire_stations.values()]
        all_lats.extend([loc[0] for loc in emergency_locations])
        all_lons = [coord[1] for coord in fire_stations.values()]
        all_lons.extend([loc[1] for loc in emergency_locations])
        
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        
        # Create grid nodes
        lat_step = (max_lat - min_lat) / grid_size
        lon_step = (max_lon - min_lon) / grid_size
        
        grid_nodes = {}
        for i in range(grid_size):
            for j in range(grid_size):
                lat = min_lat + i * lat_step
                lon = min_lon + j * lon_step
                node_id = f"grid_{i}_{j}"
                self.add_node(node_id, (lat, lon))
                grid_nodes[node_id] = (lat, lon)
        
        # Connect grid nodes (4-connected grid)
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = f"grid_{i}_{j}"
                # Connect to right neighbor
                if j < grid_size - 1:
                    right_id = f"grid_{i}_{j+1}"
                    dist = self.calculate_distance(
                        grid_nodes[node_id],
                        grid_nodes[right_id]
                    )
                    self.add_edge(node_id, right_id, dist)
                    self.add_edge(right_id, node_id, dist)
                # Connect to bottom neighbor
                if i < grid_size - 1:
                    bottom_id = f"grid_{i+1}_{j}"
                    dist = self.calculate_distance(
                        grid_nodes[node_id],
                        grid_nodes[bottom_id]
                    )
                    self.add_edge(node_id, bottom_id, dist)
                    self.add_edge(bottom_id, node_id, dist)
        
        # Connect fire stations to nearest grid nodes
        for station_id, coords in fire_stations.items():
            self.add_node(station_id, coords)
            nearest = self._find_nearest_grid_node(coords, grid_nodes)
            if nearest:
                dist = self.calculate_distance(coords, grid_nodes[nearest])
                self.add_edge(station_id, nearest, dist)
                self.add_edge(nearest, station_id, dist)
        
        # Connect emergency locations to nearest grid nodes
        for lat, lon, call_id in emergency_locations:
            self.add_node(call_id, (lat, lon))
            nearest = self._find_nearest_grid_node((lat, lon), grid_nodes)
            if nearest:
                dist = self.calculate_distance((lat, lon), grid_nodes[nearest])
                self.add_edge(call_id, nearest, dist)
                self.add_edge(nearest, call_id, dist)
    
    def _find_nearest_grid_node(self, coords: Tuple[float, float],
                                grid_nodes: Dict[str, Tuple[float, float]]) -> str:
        """Find the nearest grid node to given coordinates."""
        min_dist = float('inf')
        nearest = None
        
        for node_id, grid_coords in grid_nodes.items():
            dist = self.calculate_distance(coords, grid_coords)
            if dist < min_dist:
                min_dist = dist
                nearest = node_id
        
        return nearest
    
    def get_graph(self) -> Dict[str, Dict[str, float]]:
        """
        Get the built graph.
        
        Returns:
            Graph dictionary: {node: {neighbor: weight, ...}, ...}
        """
        return self.graph
    
    def get_node_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """
        Get coordinates for all nodes.
        
        Returns:
            Dictionary mapping node_id to (lat, lon)
        """
        return self.node_coordinates
