"""
Fire Emergency Response Optimisation System

Main system that uses Dijkstra's algorithm to optimize fire emergency response routes.
"""

from typing import List, Tuple, Dict, Optional
from dijkstra import Dijkstra
from graph_builder import GraphBuilder
from data_loader import FireDepartmentDataLoader


class FireResponseOptimizer:
    """
    Main class for optimizing fire emergency response using Dijkstra's algorithm.
    """
    
    def __init__(self, data_path: str, graph_type: str = 'proximity', 
                 max_distance_km: float = 5.0):
        """
        Initialize the fire response optimizer.
        
        Args:
            data_path: Path to fire department calls CSV file
            graph_type: Type of graph to build ('proximity', 'fully_connected', 'grid')
            max_distance_km: Maximum distance for proximity graph edges
        """
        self.data_loader = FireDepartmentDataLoader(data_path)
        self.graph_builder = GraphBuilder()
        self.graph_type = graph_type
        self.max_distance_km = max_distance_km
        self.dijkstra = None
        self.fire_stations = {}
        self.emergency_locations = []
        
    def initialize(self):
        """Load data and build the graph."""
        print("Initializing Fire Response Optimizer...")
        
        # Load data
        self.data_loader.load_data()
        self.fire_stations = self.data_loader.get_fire_stations()
        self.emergency_locations = self.data_loader.get_emergency_locations(limit=100)
        
        print(f"Loaded {len(self.fire_stations)} fire stations")
        print(f"Loaded {len(self.emergency_locations)} emergency locations")
        
        # Build graph
        print(f"Building {self.graph_type} graph...")
        
        if self.graph_type == 'fully_connected':
            all_locations = (
                [(coords[0], coords[1], sid) for sid, coords in self.fire_stations.items()] +
                self.emergency_locations
            )
            self.graph_builder.build_fully_connected_graph(all_locations)
        
        elif self.graph_type == 'proximity':
            all_locations = (
                [(coords[0], coords[1], sid) for sid, coords in self.fire_stations.items()] +
                self.emergency_locations
            )
            self.graph_builder.build_proximity_graph(all_locations, self.max_distance_km)
        
        elif self.graph_type == 'grid':
            self.graph_builder.build_grid_graph(
                self.fire_stations,
                self.emergency_locations,
                grid_size=15
            )
        
        else:
            raise ValueError(f"Unknown graph type: {self.graph_type}")
        
        # Initialize Dijkstra with the graph
        graph = self.graph_builder.get_graph()
        self.dijkstra = Dijkstra(graph)
        
        print(f"Graph built with {len(graph)} nodes")
        print("Initialization complete!")
    
    def find_optimal_route(self, emergency_location: Tuple[float, float],
                          fire_station_id: Optional[str] = None) -> Tuple[List[str], float]:
        """
        Find optimal route from a fire station to an emergency location.
        
        Args:
            emergency_location: (latitude, longitude) of emergency
            fire_station_id: Optional specific fire station ID. If None, finds nearest.
        
        Returns:
            Tuple of (path, distance):
            - path: List of node IDs representing the route
            - distance: Total distance in kilometers
        """
        if self.dijkstra is None:
            self.initialize()
        
        # Find or create emergency node
        emergency_node = self._find_or_create_emergency_node(emergency_location)
        
        if fire_station_id:
            # Use specified fire station
            if fire_station_id not in self.fire_stations:
                raise ValueError(f"Fire station {fire_station_id} not found")
            station_node = fire_station_id
        else:
            # Find nearest fire station
            station_node, _, _ = self.dijkstra.find_nearest_fire_station(
                emergency_node,
                list(self.fire_stations.keys())
            )
            print(f"Selected nearest fire station: {station_node}")
        
        # Find shortest path using Dijkstra
        path, distance = self.dijkstra.find_shortest_path(station_node, emergency_node)
        
        return path, distance
    
    def find_nearest_fire_station(self, emergency_location: Tuple[float, float]) -> Tuple[str, float, List[str]]:
        """
        Find the nearest fire station to an emergency location.
        
        Args:
            emergency_location: (latitude, longitude) of emergency
        
        Returns:
            Tuple of (station_id, distance, path):
            - station_id: ID of nearest fire station
            - distance: Distance in kilometers
            - path: Route from station to emergency
        """
        if self.dijkstra is None:
            self.initialize()
        
        emergency_node = self._find_or_create_emergency_node(emergency_location)
        
        station_id, distance, path = self.dijkstra.find_nearest_fire_station(
            emergency_node,
            list(self.fire_stations.keys())
        )
        
        return station_id, distance, path
    
    def optimize_multiple_emergencies(self, emergency_locations: List[Tuple[float, float]]) -> Dict:
        """
        Optimize routes for multiple emergencies.
        
        Args:
            emergency_locations: List of (lat, lon) tuples
        
        Returns:
            Dictionary with optimization results for each emergency
        """
        results = {}
        
        for i, location in enumerate(emergency_locations):
            try:
                station_id, distance, path = self.find_nearest_fire_station(location)
                results[f"emergency_{i+1}"] = {
                    'location': location,
                    'assigned_station': station_id,
                    'distance_km': distance,
                    'path': path,
                    'path_length': len(path)
                }
            except Exception as e:
                results[f"emergency_{i+1}"] = {
                    'location': location,
                    'error': str(e)
                }
        
        return results
    
    def _find_or_create_emergency_node(self, location: Tuple[float, float]) -> str:
        """
        Find existing node near location or create a new one.
        
        Args:
            location: (lat, lon) tuple
        
        Returns:
            Node ID
        """
        coords = self.graph_builder.get_node_coordinates()
        
        # Find nearest existing node
        min_dist = float('inf')
        nearest_node = None
        
        for node_id, node_coords in coords.items():
            dist = self.graph_builder.calculate_distance(location, node_coords)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id
        
        # If very close to existing node, use it
        if min_dist < 0.1:  # Within 100m
            return nearest_node
        
        # Otherwise, create new node and connect to nearest
        new_node_id = f"emergency_{len(coords)}"
        self.graph_builder.add_node(new_node_id, location)
        
        if nearest_node:
            dist = self.graph_builder.calculate_distance(location, coords[nearest_node])
            if dist <= self.max_distance_km:
                self.graph_builder.add_edge(new_node_id, nearest_node, dist)
                self.graph_builder.add_edge(nearest_node, new_node_id, dist)
        
        # Reinitialize Dijkstra with updated graph
        self.dijkstra = Dijkstra(self.graph_builder.get_graph())
        
        return new_node_id
    
    def get_statistics(self) -> Dict:
        """Get statistics about the system."""
        if self.dijkstra is None:
            return {"status": "Not initialized"}
        
        graph = self.graph_builder.get_graph()
        total_edges = sum(len(neighbors) for neighbors in graph.values())
        
        return {
            'num_nodes': len(graph),
            'num_edges': total_edges,
            'num_fire_stations': len(self.fire_stations),
            'num_emergency_locations': len(self.emergency_locations),
            'graph_type': self.graph_type
        }
