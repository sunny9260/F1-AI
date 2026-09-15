"""
Corner-Delta Engine
Analyzes telemetry data to detect corners and compute performance deltas between laps.
Used to identify where a driver loses time compared to a reference lap.

Usage:
    python corner_analysis.py --driver_lap data/VER_Monza_2024_fastest_lap.csv --reference_lap data/PER_Monza_2024_fastest_lap.csv
"""

import argparse
import os
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, List, Tuple


def detect_corners(telemetry: pd.DataFrame, min_speed_drop: float = 30.0, min_corner_duration: float = 2.0) -> List[Dict]:
    """
    Detect corners by finding local minima in the Speed trace along Distance.
    
    Args:
        telemetry: DataFrame with Distance, Speed, Time columns
        min_speed_drop: Minimum speed drop (km/h) to consider a corner
        min_corner_duration: Minimum duration (seconds) for a valid corner
    
    Returns:
        List of corner dictionaries with entry, apex, exit info
    """
    speed = telemetry['Speed'].values
    distance = telemetry['Distance'].values
    time = telemetry['Time'].values
    
    # Find speed minima (potential corner apexes)
    # Use negative speed to find minima as peaks
    peaks, properties = find_peaks(-speed, prominence=min_speed_drop, distance=10)
    
    corners = []
    for i, peak_idx in enumerate(peaks):
        apex_distance = distance[peak_idx]
        apex_speed = speed[peak_idx]
        apex_time = time[peak_idx]
        
        # Find corner entry (start of braking)
        # Look backward from apex for where speed starts dropping significantly
        entry_idx = peak_idx
        entry_speed = speed[peak_idx]
        while entry_idx > 0 and (entry_speed - speed[entry_idx]) < min_speed_drop * 0.5:
            entry_idx -= 1
            entry_speed = speed[entry_idx]
        
        # Find corner exit (end of acceleration)
        # Look forward from apex for where speed reaches near entry speed
        exit_idx = peak_idx
        exit_speed = speed[peak_idx]
        target_speed = min(entry_speed * 0.95, speed[peak_idx] + min_speed_drop)
        while exit_idx < len(speed) - 1 and speed[exit_idx] < target_speed:
            exit_idx += 1
            exit_speed = speed[exit_idx]
        
        # Calculate corner duration
        time_diff = time[exit_idx] - time[entry_idx]
        corner_duration = time_diff.total_seconds() if hasattr(time_diff, 'total_seconds') else float(time_diff) / 1e9
        
        # Only keep corners with sufficient duration
        if corner_duration >= min_corner_duration:
            corners.append({
                'corner_number': i + 1,
                'entry_distance': distance[entry_idx],
                'apex_distance': apex_distance,
                'exit_distance': distance[exit_idx],
                'entry_speed': speed[entry_idx],
                'apex_speed': apex_speed,
                'exit_speed': speed[exit_idx],
                'entry_time': time[entry_idx],
                'apex_time': time[peak_idx],
                'exit_time': time[exit_idx],
                'duration': corner_duration
            })
    
    return corners


def compute_corner_deltas(driver_corners: List[Dict], reference_corners: List[Dict]) -> List[Dict]:
    """
    Compute performance deltas between driver and reference corners.
    
    Args:
        driver_corners: Corner data from driver's lap
        reference_corners: Corner data from reference lap
    
    Returns:
        List of corner comparison dictionaries with deltas
    """
    if len(driver_corners) != len(reference_corners):
        print(f"Warning: Corner count mismatch - driver: {len(driver_corners)}, reference: {len(reference_corners)}")
    
    corner_comparisons = []
    min_corners = min(len(driver_corners), len(reference_corners))
    
    for i in range(min_corners):
        driver = driver_corners[i]
        reference = reference_corners[i]
        
        # Brake point delta (distance difference)
        brake_point_delta = driver['entry_distance'] - reference['entry_distance']
        
        # Min corner speed delta
        min_speed_delta = driver['apex_speed'] - reference['apex_speed']
        
        # Time delta through corner
        driver_corner_time = driver['duration']
        reference_corner_time = reference['duration']
        time_delta = driver_corner_time - reference_corner_time
        
        corner_comparisons.append({
            'corner_number': i + 1,
            'brake_point_delta_m': brake_point_delta,
            'min_speed_delta_kmh': min_speed_delta,
            'corner_time_delta_s': time_delta,
            'driver_entry_speed': driver['entry_speed'],
            'driver_apex_speed': driver['apex_speed'],
            'driver_exit_speed': driver['exit_speed'],
            'ref_entry_speed': reference['entry_speed'],
            'ref_apex_speed': reference['apex_speed'],
            'ref_exit_speed': reference['exit_speed'],
            'time_loss_rank': abs(time_delta)  # For ranking by impact
        })
    
    return corner_comparisons


def compute_consistency_stats(lap_summary: pd.DataFrame) -> Dict:
    """
    Compute lap-to-lap consistency statistics from lap summary data.
    
    Args:
        lap_summary: DataFrame with LapNumber, LapTime, Sector1Time, Sector2Time, Sector3Time
    
    Returns:
        Dictionary with consistency statistics
    """
    # Convert lap times to seconds for analysis
    lap_times = lap_summary['LapTime'].dt.total_seconds()
    sector1_times = lap_summary['Sector1Time'].dt.total_seconds()
    sector2_times = lap_summary['Sector2Time'].dt.total_seconds()
    sector3_times = lap_summary['Sector3Time'].dt.total_seconds()
    
    consistency_stats = {
        'total_laps': len(lap_summary),
        'lap_time_mean_s': lap_times.mean(),
        'lap_time_std_s': lap_times.std(),
        'lap_time_variance': lap_times.var(),
        'sector1_mean_s': sector1_times.mean(),
        'sector1_std_s': sector1_times.std(),
        'sector2_mean_s': sector2_times.mean(),
        'sector2_std_s': sector2_times.std(),
        'sector3_mean_s': sector3_times.mean(),
        'sector3_std_s': sector3_times.std(),
        'most_variable_sector': max([
            ('Sector 1', sector1_times.std()),
            ('Sector 2', sector2_times.std()),
            ('Sector 3', sector3_times.std())
        ], key=lambda x: x[1])[0]
    }
    
    return consistency_stats


def get_telemetry_at_corners(telemetry: pd.DataFrame, corners: List[Dict]) -> pd.DataFrame:
    """
    Extract throttle, brake, and gear data at corner entry, apex, and exit.
    
    Args:
        telemetry: Full telemetry DataFrame
        corners: List of corner dictionaries
    
    Returns:
        DataFrame with corner-specific telemetry data
    """
    corner_data = []
    
    for corner in corners:
        # Find closest telemetry points to corner markers
        entry_row = telemetry.iloc[(telemetry['Distance'] - corner['entry_distance']).abs().argsort()[:1]]
        apex_row = telemetry.iloc[(telemetry['Distance'] - corner['apex_distance']).abs().argsort()[:1]]
        exit_row = telemetry.iloc[(telemetry['Distance'] - corner['exit_distance']).abs().argsort()[:1]]
        
        corner_data.append({
            'corner_number': corner['corner_number'],
            'entry_throttle': entry_row['Throttle'].values[0] if len(entry_row) > 0 else 0,
            'entry_brake': entry_row['Brake'].values[0] if len(entry_row) > 0 else 0,
            'entry_gear': entry_row['nGear'].values[0] if len(entry_row) > 0 else 0,
            'apex_throttle': apex_row['Throttle'].values[0] if len(apex_row) > 0 else 0,
            'apex_brake': apex_row['Brake'].values[0] if len(apex_row) > 0 else 0,
            'apex_gear': apex_row['nGear'].values[0] if len(apex_row) > 0 else 0,
            'exit_throttle': exit_row['Throttle'].values[0] if len(exit_row) > 0 else 0,
            'exit_brake': exit_row['Brake'].values[0] if len(exit_row) > 0 else 0,
            'exit_gear': exit_row['nGear'].values[0] if len(exit_row) > 0 else 0,
        })
    
    return pd.DataFrame(corner_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver_lap", type=str, required=True, help="Path to driver's telemetry CSV")
    parser.add_argument("--reference_lap", type=str, required=True, help="Path to reference telemetry CSV")
    parser.add_argument("--lap_summary", type=str, help="Path to lap summary CSV for consistency analysis")
    parser.add_argument("--out", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.out, exist_ok=True)
    
    print(f"Loading telemetry data...")
    driver_tel = pd.read_csv(args.driver_lap)
    reference_tel = pd.read_csv(args.reference_lap)
    
    # Convert Time column to timedelta if it's not already
    if 'Time' in driver_tel.columns:
        driver_tel['Time'] = pd.to_timedelta(driver_tel['Time'])
    if 'Time' in reference_tel.columns:
        reference_tel['Time'] = pd.to_timedelta(reference_tel['Time'])
    
    # Ensure numeric columns are properly typed
    for col in ['Speed', 'Throttle', 'Brake', 'nGear', 'RPM', 'DRS', 'Distance', 'X', 'Y']:
        if col in driver_tel.columns:
            driver_tel[col] = pd.to_numeric(driver_tel[col], errors='coerce')
        if col in reference_tel.columns:
            reference_tel[col] = pd.to_numeric(reference_tel[col], errors='coerce')
    
    print(f"Detecting corners in driver lap...")
    driver_corners = detect_corners(driver_tel)
    print(f"Found {len(driver_corners)} corners")
    
    print(f"Detecting corners in reference lap...")
    reference_corners = detect_corners(reference_tel)
    print(f"Found {len(reference_corners)} corners")
    
    print(f"Computing corner deltas...")
    corner_deltas = compute_corner_deltas(driver_corners, reference_corners)
    
    # Get throttle/brake/gear data at corners
    driver_corner_tel = get_telemetry_at_corners(driver_tel, driver_corners)
    reference_corner_tel = get_telemetry_at_corners(reference_tel, reference_corners)
    
    # Combine corner data
    corner_df = pd.DataFrame(corner_deltas)
    corner_df = pd.concat([corner_df, driver_corner_tel.drop('corner_number', axis=1)], axis=1)
    
    # Save corner analysis
    corner_path = f"{args.out}/corner_analysis.csv"
    corner_df.to_csv(corner_path, index=False)
    print(f"Corner analysis saved to {corner_path}")
    
    # Compute consistency stats if lap summary provided
    if args.lap_summary:
        print(f"Computing consistency statistics...")
        lap_summary = pd.read_csv(args.lap_summary)
        
        # Convert time columns to timedelta
        for col in ['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']:
            if col in lap_summary.columns:
                lap_summary[col] = pd.to_timedelta(lap_summary[col])
        
        consistency_stats = compute_consistency_stats(lap_summary)
        
        # Save consistency stats
        import json
        consistency_path = f"{args.out}/consistency_stats.json"
        with open(consistency_path, 'w') as f:
            json.dump(consistency_stats, f, indent=2)
        print(f"Consistency statistics saved to {consistency_path}")
    
    print(f"\nTop 5 corners by time loss:")
    top_corners = corner_df.sort_values('time_loss_rank', ascending=False).head(5)
    print(top_corners[['corner_number', 'corner_time_delta_s', 'brake_point_delta_m', 'min_speed_delta_kmh']].to_string(index=False))


if __name__ == "__main__":
    main()