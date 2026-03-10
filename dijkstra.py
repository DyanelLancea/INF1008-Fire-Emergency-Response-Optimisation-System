"""
Dijkstra's Algorithm Implementation for Fire Emergency Response Optimization

This module implements Dijkstra's algorithm to find the shortest path
from fire stations to emergency locations in a weighted graph.
"""

import heapq
from typing import Dict, List, Tuple, Optional, Set


class Dijkstra:
    """
    Dijkstra's Algorithm for finding shortest paths in a weighted graph.
    
    The algorithm finds the shortest path from a source node to all other nodes
    in a graph with non-negative edge weights.
    """
    
    def __init__(self, graph: Dict):
        """
        Initialize Dijkstra's algorithm with a graph.
        
        Args:
            graph: Dictionary representing the graph
                   Format: {node: {neighbor: weight, ...}, ...}
                   Example: {'A': {'B': 5, 'C': 3}, 'B': {'A': 5, 'D': 2}}
        """
        self.graph = graph
    
    def shortest_path(self, start: str, end: Optional[str] = None) -> Tuple[Dict, Dict]:
        """
        Find shortest path(s) using Dijkstra's algorithm.
        
        Args:
            start: Starting node (fire station location)
            end: Optional target node (emergency location). If None, finds paths to all nodes.
        
        Returns:
            Tuple of (distances, previous_nodes):
            - distances: Dictionary mapping each node to its shortest distance from start
            - previous_nodes: Dictionary mapping each node to its previous node in shortest path
        """
        # Initialize distances: all nodes start with infinite distance
        distances = {node: float('inf') for node in self.graph}
        distances[start] = 0
        
        # Track previous node in shortest path for reconstruction
        previous = {node: None for node in self.graph}
        
        # Priority queue: (distance, node)
        # We use a min-heap to always process the closest unvisited node
        pq = [(0, start)]
        visited: Set[str] = set()
        
        while pq:
            # Get the node with minimum distance
            current_dist, current = heapq.heappop(pq)
            
            # Skip if already visited (we may have added same node multiple times)
            if current in visited:
                continue
            
            visited.add(current)
            
            # Early termination if we found the target
            if end and current == end:
                break
            
            # If current distance is infinity, node is unreachable
            if current_dist == float('inf'):
                break
            
            # Explore neighbors
            if current in self.graph:
                for neighbor, weight in self.graph[current].items():
                    if neighbor in visited:
                        continue
                    
                    # Calculate new distance through current node
                    new_dist = current_dist + weight
                    
                    # If we found a shorter path, update it
                    if new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        previous[neighbor] = current
                        heapq.heappush(pq, (new_dist, neighbor))
        
        return distances, previous
    
    def reconstruct_path(self, previous: Dict, start: str, end: str) -> List[str]:
        """
        Reconstruct the shortest path from start to end using previous nodes.
        
        Args:
            previous: Dictionary mapping each node to its previous node
            start: Starting node
            end: Target node
        
        Returns:
            List of nodes representing the path from start to end
        """
        path = []
        current = end
        
        # Trace back from end to start
        while current is not None:
            path.append(current)
            current = previous.get(current)
        
        # Reverse to get path from start to end
        path.reverse()
        
        # Check if path exists (start and end are connected)
        if path[0] != start:
            return []  # No path exists
        
        return path
    
    def find_shortest_path(self, start: str, end: str) -> Tuple[List[str], float]:
        """
        Find the shortest path from start to end and return both path and distance.
        
        Args:
            start: Starting node (fire station)
            end: Target node (emergency location)
        
        Returns:
            Tuple of (path, distance):
            - path: List of nodes representing the shortest path
            - distance: Total distance/weight of the path
        """
        distances, previous = self.shortest_path(start, end)
        path = self.reconstruct_path(previous, start, end)
        distance = distances.get(end, float('inf'))
        
        return path, distance
    
    def find_nearest_fire_station(self, emergency_location: str, 
                                   fire_stations: List[str]) -> Tuple[str, float, List[str]]:
        """
        Find the nearest fire station to an emergency location.
        
        Args:
            emergency_location: Node representing the emergency location
            fire_stations: List of fire station node IDs
        
        Returns:
            Tuple of (nearest_station, distance, path):
            - nearest_station: ID of the nearest fire station
            - distance: Distance to the nearest station
            - path: Path from nearest station to emergency location
        """
        if emergency_location not in self.graph:
            raise ValueError(f"Emergency location {emergency_location} not in graph")
        
        best_station = None
        best_distance = float('inf')
        best_path = []
        
        # Check distance from each fire station
        for station in fire_stations:
            if station not in self.graph:
                continue
            
            path, distance = self.find_shortest_path(station, emergency_location)
            
            if distance < best_distance:
                best_distance = distance
                best_station = station
                best_path = path
        
        if best_station is None:
            raise ValueError("No reachable fire station found")
        
        return best_station, best_distance, best_path
