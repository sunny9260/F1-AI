"""
Track Visualization Module
Creates animated 2D track maps with car position driven by telemetry data.
Supports color-coding by speed, braking, and throttle state.

Usage:
    python track_animation.py --telemetry data/VER_Monza_2024_fastest_lap.csv --output reports/track_animation.mp4
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle
from typing import Optional, Tuple


def create_track_map(telemetry: pd.DataFrame, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
    """
    Create a static track map from telemetry X/Y coordinates.
    
    Args:
        telemetry: DataFrame with X, Y, Speed, Throttle, Brake columns
        figsize: Figure size (width, height)
    
    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot track outline
    ax.plot(telemetry['X'], telemetry['Y'], color='gray', linewidth=2, alpha=0.5)
    
    # Color-code by speed
    scatter = ax.scatter(telemetry['X'], telemetry['Y'], c=telemetry['Speed'], 
                        cmap='jet', s=10, alpha=0.7)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Speed (km/h)', rotation=270, labelpad=20)
    
    # Formatting
    ax.set_aspect('equal')
    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_title('Track Map - Speed Color-Coded')
    ax.grid(True, alpha=0.3)
    
    return fig


def create_animated_track(telemetry: pd.DataFrame, output_path: str, 
                         figsize: Tuple[int, int] = (12, 8),
                         color_by: str = 'speed',
                         reference_telemetry: Optional[pd.DataFrame] = None,
                         fps: int = 30) -> None:
    """
    Create an animated track visualization with car position driven by telemetry.
    
    Args:
        telemetry: DataFrame with Time, Distance, X, Y, Speed, Throttle, Brake columns
        output_path: Path to save the animation (MP4 or GIF)
        figsize: Figure size (width, height)
        color_by: What to color-code by ('speed', 'brake', 'throttle')
        reference_telemetry: Optional reference lap to overlay for comparison
        fps: Frames per second for animation
    """
    # Downsample telemetry for smoother animation
    sample_rate = max(1, len(telemetry) // 500)  # Target ~500 frames
    tel = telemetry.iloc[::sample_rate].reset_index(drop=True)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot reference lap if provided
    if reference_telemetry is not None:
        ref_tel = reference_telemetry.iloc[::sample_rate].reset_index(drop=True)
        ax.plot(ref_tel['X'], ref_tel['Y'], color='blue', linewidth=2, 
                alpha=0.5, label='Reference Lap')
    
    # Plot track outline
    ax.plot(tel['X'], tel['Y'], color='gray', linewidth=2, alpha=0.3, label='Track')
    
    # Car marker
    car_marker = Circle((tel['X'].iloc[0], tel['Y'].iloc[0]), 50, 
                       color='red', zorder=10, label='Car')
    ax.add_patch(car_marker)
    
    # Trail (recent positions)
    trail_length = 20
    trail, = ax.plot([], [], color='red', linewidth=3, alpha=0.7)
    
    # Info text
    info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, 
                       verticalalignment='top', fontsize=10,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Color mapping based on choice
    if color_by == 'speed':
        cmap = plt.get_cmap('jet')
        norm = plt.Normalize(vmin=tel['Speed'].min(), vmax=tel['Speed'].max())
        def get_color(speed):
            return cmap(norm(speed))
        color_label = 'Speed (km/h)'
    elif color_by == 'brake':
        cmap = plt.get_cmap('Reds')
        norm = plt.Normalize(vmin=0, vmax=1)
        def get_color(brake):
            return cmap(norm(brake))
        color_label = 'Brake'
    elif color_by == 'throttle':
        cmap = plt.get_cmap('Greens')
        norm = plt.Normalize(vmin=0, vmax=100)
        def get_color(throttle):
            return cmap(norm(throttle))
        color_label = 'Throttle (%)'
    else:
        def get_color(val):
            return 'red'
        color_label = 'Unknown'
    
    # Set up colorbar if needed
    if color_by in ['speed', 'brake', 'throttle']:
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label(color_label, rotation=270, labelpad=20)
    
    # Formatting
    ax.set_aspect('equal')
    ax.set_xlabel('X Position')
    ax.set_ylabel('Y Position')
    ax.set_title(f'Track Animation - Color by {color_by}')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    def update(frame):
        # Update car position
        car_marker.center = (tel['X'].iloc[frame], tel['Y'].iloc[frame])
        
        # Update trail
        start_idx = max(0, frame - trail_length)
        trail.set_data(tel['X'].iloc[start_idx:frame+1], 
                      tel['Y'].iloc[start_idx:frame+1])
        
        # Update car color based on telemetry
        if color_by == 'speed':
            car_marker.set_color(get_color(tel['Speed'].iloc[frame]))
        elif color_by == 'brake':
            car_marker.set_color(get_color(tel['Brake'].iloc[frame]))
        elif color_by == 'throttle':
            car_marker.set_color(get_color(tel['Throttle'].iloc[frame]))
        
        # Update info text
        current_time = tel['Time'].iloc[frame] if 'Time' in tel.columns else frame
        # Handle different time formats
        if hasattr(current_time, 'total_seconds'):
            time_str = f"{current_time.total_seconds():.2f}s"
        elif isinstance(current_time, str):
            time_str = current_time
        else:
            time_str = f"{float(current_time):.2f}s"
        
        info_text.set_text(
            f"Time: {time_str}\n"
            f"Speed: {tel['Speed'].iloc[frame]:.1f} km/h\n"
            f"Throttle: {tel['Throttle'].iloc[frame]:.1f}%\n"
            f"Brake: {tel['Brake'].iloc[frame]:.0f}\n"
            f"Gear: {tel['nGear'].iloc[frame]}"
        )
        
        return car_marker, trail, info_text
    
    # Create animation
    anim = animation.FuncAnimation(fig, update, frames=len(tel), 
                                   interval=1000/fps, blit=True)
    
    # Save animation
    print(f"Saving animation to {output_path}...")
    if output_path.endswith('.mp4'):
        anim.save(output_path, writer='ffmpeg', fps=fps, dpi=100)
    elif output_path.endswith('.gif'):
        anim.save(output_path, writer='pillow', fps=fps, dpi=100)
    else:
        anim.save(output_path + '.mp4', writer='ffmpeg', fps=fps, dpi=100)
    
    print(f"Animation saved successfully!")
    plt.close()


def create_comparison_plot(driver_tel: pd.DataFrame, reference_tel: pd.DataFrame, 
                          output_path: str, figsize: Tuple[int, int] = (15, 10)) -> None:
    """
    Create a side-by-side comparison of two laps with telemetry overlays.
    
    Args:
        driver_tel: Driver's telemetry DataFrame
        reference_tel: Reference telemetry DataFrame
        output_path: Path to save the comparison plot
        figsize: Figure size (width, height)
    """
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    
    # Track map comparison
    ax1 = axes[0, 0]
    ax1.plot(reference_tel['X'], reference_tel['Y'], color='blue', 
             linewidth=2, alpha=0.7, label='Reference')
    ax1.plot(driver_tel['X'], driver_tel['Y'], color='red', 
             linewidth=2, alpha=0.7, label='Driver')
    ax1.set_aspect('equal')
    ax1.set_title('Track Map Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Speed trace comparison
    ax2 = axes[0, 1]
    ax2.plot(reference_tel['Distance'], reference_tel['Speed'], 
             color='blue', alpha=0.7, label='Reference')
    ax2.plot(driver_tel['Distance'], driver_tel['Speed'], 
             color='red', alpha=0.7, label='Driver')
    ax2.set_xlabel('Distance (m)')
    ax2.set_ylabel('Speed (km/h)')
    ax2.set_title('Speed Trace')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Throttle comparison
    ax3 = axes[1, 0]
    ax3.plot(reference_tel['Distance'], reference_tel['Throttle'], 
             color='blue', alpha=0.7, label='Reference')
    ax3.plot(driver_tel['Distance'], driver_tel['Throttle'], 
             color='red', alpha=0.7, label='Driver')
    ax3.set_xlabel('Distance (m)')
    ax3.set_ylabel('Throttle (%)')
    ax3.set_title('Throttle Trace')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Brake comparison
    ax4 = axes[1, 1]
    ax4.plot(reference_tel['Distance'], reference_tel['Brake'], 
             color='blue', alpha=0.7, label='Reference')
    ax4.plot(driver_tel['Distance'], driver_tel['Brake'], 
             color='red', alpha=0.7, label='Driver')
    ax4.set_xlabel('Distance (m)')
    ax4.set_ylabel('Brake (0/1)')
    ax4.set_title('Brake Trace')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Comparison plot saved to {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--telemetry", type=str, required=True, help="Path to telemetry CSV")
    parser.add_argument("--reference", type=str, help="Path to reference telemetry CSV for comparison")
    parser.add_argument("--output", type=str, default="reports/track_animation.mp4", help="Output path")
    parser.add_argument("--color_by", type=str, default="speed", 
                       choices=['speed', 'brake', 'throttle'], help="Color coding for animation")
    parser.add_argument("--static", action="store_true", help="Create static track map instead of animation")
    parser.add_argument("--comparison", action="store_true", help="Create comparison plot with reference")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for animation")
    args = parser.parse_args()
    
    # Load telemetry
    print(f"Loading telemetry from {args.telemetry}...")
    telemetry = pd.read_csv(args.telemetry)
    
    # Create output directory if needed
    import os
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    
    if args.static:
        print("Creating static track map...")
        fig = create_track_map(telemetry)
        # Ensure output has .png extension for static images
        output_path = args.output if args.output.endswith('.png') else args.output.rsplit('.', 1)[0] + '.png'
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Static track map saved to {output_path}")
        plt.close()
    
    elif args.comparison and args.reference:
        print(f"Loading reference telemetry from {args.reference}...")
        reference_tel = pd.read_csv(args.reference)
        print("Creating comparison plot...")
        # Ensure output has .png extension for comparison plots
        output_path = args.output if args.output.endswith('.png') else args.output.rsplit('.', 1)[0] + '.png'
        create_comparison_plot(telemetry, reference_tel, output_path)
    
    else:
        reference_tel = None
        if args.reference:
            print(f"Loading reference telemetry from {args.reference}...")
            reference_tel = pd.read_csv(args.reference)
        
        print("Creating animated track visualization...")
        create_animated_track(telemetry, args.output, color_by=args.color_by, 
                            reference_telemetry=reference_tel, fps=args.fps)


if __name__ == "__main__":
    main()