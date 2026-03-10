# Fire Emergency Response Optimisation System

This system uses **Dijkstra's Algorithm** to optimize fire emergency response routes in San Francisco.

## Overview

The system analyzes San Francisco Fire Department call data and uses Dijkstra's algorithm to find the shortest/optimal path from fire stations to emergency locations, minimizing response time.

## Dataset

Download the dataset from: https://www.kaggle.com/datasets/jacopoferretti/san-francisco-fire-department-calls-dataset

Place the dataset file(s) in the `data/` directory.

## How Dijkstra's Algorithm is Used

Dijkstra's algorithm is implemented to solve the **shortest path problem**:

1. **Graph Representation**: The road network is represented as a weighted graph where:
   - **Nodes** = Intersections/Locations (fire stations, emergency locations)
   - **Edges** = Roads connecting locations
   - **Edge Weights** = Distance or travel time between locations

2. **Optimization Goal**: Find the shortest path from a fire station to an emergency location to minimize response time.

3. **Algorithm Flow**:
   - Start from the fire station (source node)
   - Use Dijkstra to find shortest path to emergency location (target node)
   - Returns the optimal route and total distance/time

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from fire_response_optimizer import FireResponseOptimizer

# Initialize the optimizer
optimizer = FireResponseOptimizer('data/fire_department_calls.csv')

# Find optimal route for an emergency
route, distance = optimizer.find_optimal_route(
    emergency_location=(37.7749, -122.4194),
    fire_station_id='Station_1'
)
```

## Project Structure

```
.
├── dijkstra.py              # Dijkstra's algorithm implementation
├── graph_builder.py         # Builds graph from fire station and location data
├── data_loader.py           # Loads and processes fire department calls
├── fire_response_optimizer.py  # Main optimization system
├── main.py                  # Example usage
└── requirements.txt
```
