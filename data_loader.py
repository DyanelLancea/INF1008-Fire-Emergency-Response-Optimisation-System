"""
Data Loader for San Francisco Fire Department Calls Dataset

This module loads and processes the fire department calls dataset.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import os
import re


class FireDepartmentDataLoader:
    """
    Loads and processes San Francisco Fire Department calls data.
    """
    
    def __init__(self, data_path: str):
        """
        Initialize the data loader.
        
        Args:
            data_path: Path to the CSV file containing fire department calls
        """
        self.data_path = data_path
        self.df: Optional[pd.DataFrame] = None
        self.fire_stations: Dict = {}
        
    def load_data(self) -> pd.DataFrame:
        """
        Load the fire department calls dataset.
        
        Returns:
            DataFrame containing fire department calls
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(
                f"Dataset not found at {self.data_path}. "
                f"Please download from: https://www.kaggle.com/datasets/jacopoferretti/san-francisco-fire-department-calls-dataset"
            )
        
        print(f"Loading data from {self.data_path}...")
        # low_memory=False avoids pandas DtypeWarning for mixed-type columns.
        self.df = pd.read_csv(self.data_path, low_memory=False)
        print(f"Loaded {len(self.df)} records")
        
        return self.df
    
    def get_emergency_locations(self, limit: Optional[int] = None) -> List[Tuple[float, float, str]]:
        """
        Extract emergency locations from the dataset.
        
        Args:
            limit: Optional limit on number of locations to return
        
        Returns:
            List of tuples: (latitude, longitude, call_id)
        """
        if self.df is None:
            self.load_data()
        
        # Try to find latitude/longitude columns (common names)
        lat_col = None
        lon_col = None
        
        for col in self.df.columns:
            col_lower = col.lower()
            if 'lat' in col_lower:
                lat_col = col
            if 'lon' in col_lower or 'lng' in col_lower:
                lon_col = col
        
        if lat_col is None or lon_col is None:
            # Many Kaggle exports store coordinates inside a single text column.
            # Example: "(37.7765408927183, -122.417501464907)"
            if "Location" in self.df.columns:
                locations = []

                call_id_col = None
                for col in ['Call Number', 'CallNumber', 'Incident Number', 'id']:
                    if col in self.df.columns:
                        call_id_col = col
                        break
                row_id_col = "RowID" if "RowID" in self.df.columns else None

                # Avoid scanning the entire dataset when a limit is provided.
                # If parsing fails for some rows, scanning extra rows increases the chance
                # of reaching the requested number of emergencies.
                max_scan = len(self.df) if limit is None else min(len(self.df), limit * 20)
                candidate_df = self.df.head(max_scan)

                # Assignment requirement: filter only fire incidents.
                # In this dataset, `CallTypeGroup` appears to be empty, so use `CallType`.
                if "CallType" in self.df.columns:
                    fire_mask = candidate_df["CallType"].astype(str).str.contains(
                        "Fire", case=False, na=False
                    )
                    if fire_mask.any():
                        candidate_df = candidate_df[fire_mask]

                for idx, row in candidate_df.iterrows():
                    parsed = self._parse_lat_lon_from_location(row.get("Location"))
                    if parsed is None:
                        continue

                    lat, lon = parsed
                    base_call_id = str(row[call_id_col]) if call_id_col else "call"
                    unique_suffix = str(row[row_id_col]) if row_id_col else str(idx)
                    # Node IDs must be unique; otherwise graph nodes get overwritten.
                    call_id = f"{base_call_id}_{unique_suffix}"
                    locations.append((lat, lon, call_id))

                    if limit is not None and len(locations) >= limit:
                        break

                # If we couldn't parse enough rows, fall back to sample locations.
                if limit is not None and len(locations) < limit:
                    remaining = limit - len(locations)
                    locations.extend(self._create_sample_locations(remaining))

                return locations

            # If the dataset doesn't contain coordinates anywhere, create sample locations.
            print("Warning: Latitude/Longitude columns not found (and Location parsing failed). Using sample data.")
            return self._create_sample_locations(limit)
        
        # Filter out rows with missing coordinates
        valid_data = self.df.dropna(subset=[lat_col, lon_col])
        
        if limit:
            valid_data = valid_data.head(limit)
        
        # Get unique call ID column if available
        call_id_col = None
        for col in ['Call Number', 'CallNumber', 'Incident Number', 'id']:
            if col in self.df.columns:
                call_id_col = col
                break
        
        locations = []
        for idx, row in valid_data.iterrows():
            lat = row[lat_col]
            lon = row[lon_col]
            base_call_id = str(row[call_id_col]) if call_id_col else "call"
            unique_suffix = str(row["RowID"]) if "RowID" in self.df.columns else str(idx)
            # Node IDs must be unique; otherwise graph nodes get overwritten.
            call_id = f"{base_call_id}_{unique_suffix}"
            locations.append((lat, lon, call_id))
        
        return locations

    def _parse_lat_lon_from_location(self, location_value) -> Optional[Tuple[float, float]]:
        """
        Parse "(lat, lon)" style coordinate strings from the dataset's "Location" column.
        Returns (lat, lon) as floats, or None if parsing fails.
        """
        if location_value is None or (isinstance(location_value, float) and np.isnan(location_value)):
            return None

        s = str(location_value)
        # Capture two floats separated by a comma, optionally wrapped in parentheses.
        # Example match: (37.7765408927183, -122.417501464907)
        match = re.search(
            r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)",
            s,
        )
        if not match:
            return None

        return float(match.group(1)), float(match.group(2))
    
    def get_fire_stations(self) -> Dict[str, Tuple[float, float]]:
        """
        Get fire station locations.
        
        Since the dataset may not include fire station locations,
        we'll use known SF fire station locations or extract from data.
        
        Returns:
            Dictionary mapping station_id to (latitude, longitude)
        """
        # San Francisco Fire Department stations (sample locations)
        # In a real implementation, you'd load this from the dataset or a separate file
        sf_fire_stations = {
            'Station_1': (37.7849, -122.4094),
            'Station_2': (37.7749, -122.4194),
            'Station_3': (37.7649, -122.4294),
            'Station_4': (37.7549, -122.4394),
            'Station_5': (37.7449, -122.4494),
            'Station_6': (37.7849, -122.3894),
            'Station_7': (37.7749, -122.3994),
            'Station_8': (37.7649, -122.4094),
        }
        
        self.fire_stations = sf_fire_stations
        return sf_fire_stations
    
    def _create_sample_locations(self, limit: Optional[int] = None) -> List[Tuple[float, float, str]]:
        """
        Create sample emergency locations if coordinates are not in dataset.
        
        Args:
            limit: Number of sample locations to create
        
        Returns:
            List of sample (lat, lon, call_id) tuples
        """
        # Sample locations in San Francisco area
        np.random.seed(42)
        base_lat, base_lon = 37.7749, -122.4194  # SF center
        
        num_locations = limit if limit else 50
        locations = []
        
        for i in range(num_locations):
            # Random locations within ~10km of SF center
            lat = base_lat + np.random.uniform(-0.1, 0.1)
            lon = base_lon + np.random.uniform(-0.1, 0.1)
            locations.append((lat, lon, f"emergency_{i+1}"))
        
        return locations
    
    def get_call_statistics(self) -> Dict:
        """
        Get statistics about fire department calls.
        
        Returns:
            Dictionary with call statistics
        """
        if self.df is None:
            self.load_data()
        
        stats = {
            'total_calls': len(self.df),
            'columns': list(self.df.columns),
            'date_range': None,
            'call_types': None
        }
        
        # Try to find date column
        for col in self.df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                    stats['date_range'] = (
                        self.df[col].min(),
                        self.df[col].max()
                    )
                break
        
        # Try to find call type column
        for col in self.df.columns:
            if 'type' in col.lower() or 'category' in col.lower():
                stats['call_types'] = self.df[col].value_counts().to_dict()
                break
        
        return stats
