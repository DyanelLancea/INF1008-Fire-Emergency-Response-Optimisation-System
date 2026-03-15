"""
Demonstration of Dijkstra's Algorithm for Fire Emergency Response

This script provides a simple, step-by-step demonstration of how
Dijkstra's algorithm finds the shortest path from a fire station to an emergency.
"""

from dijkstra import Dijkstra


def demonstrate_dijkstra():
    """
    Demonstrate Dijkstra's algorithm with a simple example.
    """
    print("=" * 70)
    print("Dijkstra's Algorithm Demonstration")
    print("Fire Emergency Response Route Optimization")
    print("=" * 70)
    print()
    
    # Create a simple graph representing fire stations and locations
    # Format: {node: {neighbor: distance_in_km, ...}, ...}
    graph = {
        'Fire_Station_A': {
            'Location_1': 3.0,
            'Location_2': 5.0,
            'Location_3': 8.0
        },
        'Fire_Station_B': {
            'Location_1': 2.0,
            'Location_4': 4.0
        },
        'Location_1': {
            'Fire_Station_A': 3.0,
            'Fire_Station_B': 2.0,
            'Location_2': 1.5,
            'Emergency': 2.5
        },
        'Location_2': {
            'Fire_Station_A': 5.0,
            'Location_1': 1.5,
            'Emergency': 1.0
        },
        'Location_3': {
            'Fire_Station_A': 8.0,
            'Location_4': 3.0
        },
        'Location_4': {
            'Fire_Station_B': 4.0,
            'Location_3': 3.0,
            'Emergency': 3.5
        },
        'Emergency': {
            'Location_1': 2.5,
            'Location_2': 1.0,
            'Location_4': 3.5
        }
    }
    
    print("Graph Structure:")
    print("-" * 70)
    for node, neighbors in graph.items():
        print(f"{node}:")
        for neighbor, distance in neighbors.items():
            print(f"  -> {neighbor} (distance: {distance} km)")
    print()
    
    # Initialize Dijkstra
    dijkstra = Dijkstra(graph)
    
    # Example 1: Find shortest path from Fire Station A to Emergency
    print("Example 1: Find shortest path from Fire Station A to Emergency")
    print("-" * 70)
    start = 'Fire_Station_A'
    end = 'Emergency'
    
    path, distance = dijkstra.find_shortest_path(start, end)
    
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Shortest Path: {' -> '.join(path)}")
    print(f"Total Distance: {distance} km")
    print()
    
    # Show the calculation
    print("Path Breakdown:")
    total = 0
    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]
        edge_weight = graph[current][next_node]
        total += edge_weight
        print(f"  {current} -> {next_node}: {edge_weight} km (cumulative: {total} km)")
    print()
    
    # Example 2: Find shortest path from Fire Station B to Emergency
    print("Example 2: Find shortest path from Fire Station B to Emergency")
    print("-" * 70)
    start = 'Fire_Station_B'
    end = 'Emergency'
    
    path, distance = dijkstra.find_shortest_path(start, end)
    
    print(f"Start: {start}")
    print(f"End: {end}")
    print(f"Shortest Path: {' -> '.join(path)}")
    print(f"Total Distance: {distance} km")
    print()
    
    # Example 3: Find nearest fire station to emergency
    print("Example 3: Find nearest fire station to Emergency")
    print("-" * 70)
    fire_stations = ['Fire_Station_A', 'Fire_Station_B']
    
    station, dist, path = dijkstra.find_nearest_fire_station('Emergency', fire_stations)
    
    print(f"Emergency Location: Emergency")
    print(f"Nearest Fire Station: {station}")
    print(f"Distance: {dist} km")
    print(f"Path: {' -> '.join(path)}")
    print()
    
    # Explain the algorithm
    print("=" * 70)
    print("How Dijkstra's Algorithm Works:")
    print("=" * 70)
    print("""
1. INITIALIZATION:
   - Set distance to start node = 0
   - Set distance to all other nodes = infinity
   - Create a priority queue (min-heap) with start node

2. ITERATION:
   - Extract node with minimum distance from queue
   - Mark it as visited
   - For each unvisited neighbor:
     * Calculate new distance = current distance + edge weight
     * If new distance < existing distance:
       - Update distance
       - Add neighbor to queue with new distance
       - Record previous node for path reconstruction

3. TERMINATION:
   - Stop when target node is reached (or queue is empty)
   - Reconstruct path by following 'previous' pointers backwards

4. TIME COMPLEXITY:
   - O((V + E) log V) using binary heap
   - V = number of nodes (vertices)
   - E = number of edges
   - Efficient for finding shortest paths in weighted graphs

5. WHY IT WORKS:
   - Greedy approach: always processes closest unvisited node
   - Guarantees shortest path when all edge weights are non-negative
   - Optimal for single-source shortest path problems
    """)


if __name__ == "__main__":
    demonstrate_dijkstra()
