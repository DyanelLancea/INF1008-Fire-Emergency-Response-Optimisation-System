"""
Example usage of the Fire Emergency Response Optimisation System

This script demonstrates how to use Dijkstra's algorithm to optimize
fire emergency response routes.
"""

from fire_response_optimizer import FireResponseOptimizer
import os


def main():
    """Main example function."""
    print("=" * 60)
    print("Fire Emergency Response Optimisation System")
    print("Using Dijkstra's Algorithm for Route Optimization")
    print("=" * 60)
    print()
    
    # Path to your dataset
    # Update this path to point to your downloaded dataset
    data_path = "data/fire_dept.csv"
    
    # Check if data directory exists, create if not
    os.makedirs("data", exist_ok=True)
    
    # Initialize the optimizer
    # You can choose graph type: 'proximity', 'fully_connected', or 'grid'
    optimizer = FireResponseOptimizer(
        data_path=data_path,
        graph_type='proximity',  # or 'grid' for more realistic road network
        max_distance_km=5.0
    )
    
    try:
        # Initialize the system (loads data and builds graph)
        optimizer.initialize()
        
        # Display statistics
        stats = optimizer.get_statistics()
        print("\nSystem Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()
        
        # Example 1: Find optimal route for a specific emergency
        print("Example 1: Finding optimal route for an emergency")
        print("-" * 60)
        # Pick an incident location directly from the dataset we loaded.
        # Each entry in optimizer.emergency_locations is: (lat, lon, call_id)
        emergency_location = optimizer.emergency_locations[0][:2]
        
        try:
            dijkstra_station_id, dijkstra_distance, path = optimizer.find_nearest_fire_station(emergency_location)
            straight_station_id, straight_distance = optimizer.find_nearest_fire_station_straight_line(emergency_location)
            print(f"Emergency Location: {emergency_location}")
            # Explicit answers to key questions
            print(f"Q1: Which fire station should respond to minimise travel distance?")
            print(f"   A1 (Dijkstra): {dijkstra_station_id}")
            print(f"   Straight-line nearest (for comparison): {straight_station_id}")
            print(f"Q2: What is the shortest route from that station to the incident?")
            full_path_str = ' -> '.join(path)
            preview = ' -> '.join(path[:5]) + (" -> ..." if len(path) > 5 else "")
            print(f"   A2 (node sequence, preview): {preview}")
            print(f"   A2 (full path): {full_path_str}")
            print(f"Total travel distance along this route (Dijkstra): {dijkstra_distance:.2f} km")
            print(f"Straight-line distance to nearest station: {straight_distance:.2f} km")
            print(f"Path Length (number of nodes): {len(path)}")
        except Exception as e:
            print(f"Error: {e}")
            print("Note: This might occur if the dataset is not loaded.")
            print("Using sample data instead...")
        
        print()
        
        # Example 2: Optimize multiple emergencies
        print("Example 2: Optimizing routes for multiple emergencies")
        print("-" * 60)
        emergency_locations = [
            optimizer.emergency_locations[0][:2],
            optimizer.emergency_locations[33][:2],
            optimizer.emergency_locations[66][:2],
        ]
        
        results = optimizer.optimize_multiple_emergencies(emergency_locations)
        for emergency_id, result in results.items():
            if 'error' not in result:
                print(f"{emergency_id}:")
                print(f"  Location: {result['location']}")
                print(f"  Assigned Station: {result['assigned_station']}")
                print(f"  Distance: {result['distance_km']:.2f} km")
                print(f"  Straight-line Nearest: {result['straight_station_id']} ({result['straight_distance_km']:.2f} km)")
                print(f"  Path Length: {result['path_length']} nodes")
            else:
                print(f"{emergency_id}: Error - {result['error']}")
        
        print()
        print("=" * 60)
        print("How Dijkstra's Algorithm Works:")
        print("=" * 60)
        print("""
1. Graph Representation:
   - Nodes = Fire stations and emergency locations
   - Edges = Roads/connections between locations
   - Edge Weights = Distance or travel time

2. Algorithm Process:
   - Start from fire station (source node)
   - Use priority queue to always process closest unvisited node
   - Update distances to neighbors if shorter path found
   - Continue until reaching emergency location (target node)

3. Result:
   - Shortest path from fire station to emergency
   - Minimum distance/time for response
   - Optimal route for fastest response

4. Time Complexity: O((V + E) log V) where V = nodes, E = edges
   - Efficient for finding shortest paths in weighted graphs
        """)
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nTo use this system:")
        print("1. Download the dataset from:")
        print("   https://www.kaggle.com/datasets/jacopoferretti/san-francisco-fire-department-calls-dataset")
        print("2. Place the CSV file in the 'data/' directory")
        print("3. Update the 'data_path' variable in this script if needed")
        print("\nThe system will work with sample data for demonstration purposes.")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
