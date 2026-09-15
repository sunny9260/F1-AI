"""
F1 Telemetry AI Performance Coach - Main CLI Interface
A unified interface to run the complete F1 telemetry analysis pipeline.

Usage:
    # Complete analysis workflow
    python f1_coach.py complete --year 2024 --gp "Monza" --session R --driver VER --reference PER
    
    # Individual modules
    python f1_coach.py pipeline --year 2024 --gp "Monza" --session R --driver VER
    python f1_coach.py analyze --driver_lap data/VER_Monza_2024_fastest_lap.csv --reference_lap data/PER_Monza_2024_fastest_lap.csv
    python f1_coach.py visualize --telemetry data/VER_Monza_2024_fastest_lap.csv
    python f1_coach.py report --corner_data data/corner_analysis.csv --driver VER --gp "Monza" --year 2024
"""

import argparse
import subprocess
import sys
import os


def run_pipeline(args):
    """Run the data pipeline module."""
    cmd = [
        "python", "f1_pipeline.py",
        "--year", str(args.year),
        "--gp", args.gp,
        "--session", args.session,
        "--driver", args.driver,
        "--out", "data"
    ]
    print(f"Running data pipeline: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_analysis(args):
    """Run the corner analysis module."""
    cmd = [
        "python", "corner_analysis.py",
        "--driver_lap", args.driver_lap,
        "--reference_lap", args.reference_lap,
        "--out", "data"
    ]
    
    if args.lap_summary:
        cmd.extend(["--lap_summary", args.lap_summary])
    
    print(f"Running corner analysis: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_visualization(args):
    """Run the visualization module."""
    cmd = [
        "python", "track_animation.py",
        "--telemetry", args.telemetry,
        "--output", args.output
    ]
    
    if args.reference:
        cmd.extend(["--reference", args.reference])
    
    if args.static:
        cmd.append("--static")
    elif args.comparison:
        cmd.append("--comparison")
    
    if args.color_by:
        cmd.extend(["--color_by", args.color_by])
    
    if args.fps:
        cmd.extend(["--fps", str(args.fps)])
    
    print(f"Running visualization: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_report(args):
    """Run the AI coaching report module."""
    cmd = [
        "python", "generate_report.py",
        "--corner_data", args.corner_data,
        "--driver", args.driver,
        "--gp", args.gp,
        "--year", str(args.year),
        "--output", args.output
    ]
    
    if args.consistency:
        cmd.extend(["--consistency", args.consistency])
    
    if args.api_key:
        cmd.extend(["--api_key", args.api_key])
    
    print(f"Generating AI report: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def run_complete_workflow(args):
    """Run the complete analysis workflow from start to finish."""
    print("="*60)
    print("F1 TELEMETRY AI PERFORMANCE COACH - COMPLETE WORKFLOW")
    print("="*60)
    
    # Step 1: Data Pipeline
    print("\n[1/4] Running data pipeline...")
    pipeline_args = argparse.Namespace(
        year=args.year,
        gp=args.gp,
        session=args.session,
        driver=args.driver,
        out="data"
    )
    try:
        run_pipeline(pipeline_args)
    except subprocess.CalledProcessError as e:
        print(f"Error in data pipeline: {e}")
        return
    
    # Step 2: Corner Analysis
    print("\n[2/4] Running corner analysis...")
    
    # Generate file paths based on naming convention
    # Try both with spaces and with underscores for compatibility
    gp_clean = args.gp.replace(" ", "_")
    gp_with_space = args.gp.replace("_", " ")
    
    # Try to find existing files first
    driver_lap = None
    reference_lap = None
    lap_summary = None
    
    for gp_name in [gp_clean, gp_with_space, args.gp]:
        potential_driver_lap = f"data/{args.driver}_{gp_name}_{args.year}_fastest_lap.csv"
        potential_reference_lap = f"data/{args.reference}_{gp_name}_{args.year}_fastest_lap.csv"
        potential_lap_summary = f"data/{args.driver}_{gp_name}_{args.year}_lap_summary.csv"
        
        if driver_lap is None and os.path.exists(potential_driver_lap):
            driver_lap = potential_driver_lap
        if reference_lap is None and os.path.exists(potential_reference_lap):
            reference_lap = potential_reference_lap
        if lap_summary is None and os.path.exists(potential_lap_summary):
            lap_summary = potential_lap_summary
    
    # Fallback to cleaned names if files not found
    if driver_lap is None:
        driver_lap = f"data/{args.driver}_{gp_clean}_{args.year}_fastest_lap.csv"
    if reference_lap is None:
        reference_lap = f"data/{args.reference}_{gp_clean}_{args.year}_fastest_lap.csv"
    if lap_summary is None:
        lap_summary = f"data/{args.driver}_{gp_clean}_{args.year}_lap_summary.csv"
    
    # Check if reference lap exists, if not use the same driver's lap for self-comparison
    if not os.path.exists(reference_lap):
        print(f"Warning: Reference lap not found at {reference_lap}")
        print("Using driver's own fastest lap for self-comparison...")
        reference_lap = driver_lap
    
    analysis_args = argparse.Namespace(
        driver_lap=driver_lap,
        reference_lap=reference_lap,
        lap_summary=lap_summary
    )
    
    try:
        run_analysis(analysis_args)
    except subprocess.CalledProcessError as e:
        print(f"Error in corner analysis: {e}")
        return
    
    # Step 3: Visualization
    print("\n[3/4] Creating visualizations...")
    
    # Create static track map (more reliable than animation)
    static_output = f"reports/{args.driver}_{gp_clean}_{args.year}_track_map.png"
    static_args = argparse.Namespace(
        telemetry=driver_lap,
        reference=None,
        output=static_output,
        static=True,
        comparison=False,
        color_by="speed",
        fps=30
    )
    
    try:
        run_visualization(static_args)
    except subprocess.CalledProcessError as e:
        print(f"Error in static visualization: {e}")
        print("Continuing with remaining steps...")
    
    # Create comparison plot if reference is different
    if args.reference != args.driver:
        comp_output = f"reports/{args.driver}_vs_{args.reference}_{gp_clean}_{args.year}_comparison.png"
        comp_args = argparse.Namespace(
            telemetry=driver_lap,
            reference=reference_lap,
            output=comp_output,
            static=False,
            comparison=True,
            color_by=None,
            fps=None
        )
        
        try:
            run_visualization(comp_args)
        except subprocess.CalledProcessError as e:
            print(f"Error in comparison plot: {e}")
            print("Continuing with remaining steps...")
    
    # Step 4: AI Report
    print("\n[4/4] Generating AI performance report...")
    
    corner_data = "data/corner_analysis.csv"
    consistency_data = "data/consistency_stats.json"
    
    report_args = argparse.Namespace(
        corner_data=corner_data,
        consistency=consistency_data if os.path.exists(consistency_data) else None,
        driver=args.driver,
        gp=args.gp,
        year=args.year,
        output=f"reports/{args.driver}_{gp_clean}_{args.year}_performance_report.md",
        api_key=args.api_key
    )
    
    try:
        run_report(report_args)
    except subprocess.CalledProcessError as e:
        print(f"Error in report generation: {e}")
        return
    
    print("\n" + "="*60)
    print("COMPLETE WORKFLOW FINISHED SUCCESSFULLY!")
    print("="*60)
    print(f"\nResults saved in:")
    print(f"  - Data: data/")
    print(f"  - Reports: reports/")
    print(f"\nGenerated files:")
    print(f"  - {driver_lap}")
    print(f"  - {lap_summary}")
    print(f"  - data/corner_analysis.csv")
    print(f"  - {static_output}")
    if args.reference != args.driver:
        print(f"  - {comp_output}")
    print(f"  - {report_args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="F1 Telemetry AI Performance Coach - Unified CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete workflow
  python f1_coach.py complete --year 2024 --gp "Monza" --session R --driver VER --reference PER
  
  # Individual modules
  python f1_coach.py pipeline --year 2024 --gp "Monza" --session R --driver VER
  python f1_coach.py analyze --driver_lap data/VER_Monza_2024_fastest_lap.csv --reference_lap data/PER_Monza_2024_fastest_lap.csv
  python f1_coach.py visualize --telemetry data/VER_Monza_2024_fastest_lap.csv
  python f1_coach.py report --corner_data data/corner_analysis.csv --driver VER --gp "Monza" --year 2024
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Complete workflow command
    complete_parser = subparsers.add_parser('complete', help='Run complete analysis workflow')
    complete_parser.add_argument('--year', type=int, required=True, help='Year of the session')
    complete_parser.add_argument('--gp', type=str, required=True, help='Grand Prix name (e.g., "Monza")')
    complete_parser.add_argument('--session', type=str, default='R', help='Session type (FP1/FP2/FP3/Q/R/S)')
    complete_parser.add_argument('--driver', type=str, required=True, help='Driver code (e.g., VER)')
    complete_parser.add_argument('--reference', type=str, required=True, help='Reference driver code for comparison')
    complete_parser.add_argument('--api_key', type=str, help='Anthropic API key for report generation')
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run data pipeline only')
    pipeline_parser.add_argument('--year', type=int, required=True, help='Year of the session')
    pipeline_parser.add_argument('--gp', type=str, required=True, help='Grand Prix name')
    pipeline_parser.add_argument('--session', type=str, default='R', help='Session type')
    pipeline_parser.add_argument('--driver', type=str, required=True, help='Driver code')
    
    # Analysis command
    analysis_parser = subparsers.add_parser('analyze', help='Run corner analysis only')
    analysis_parser.add_argument('--driver_lap', type=str, required=True, help='Path to driver telemetry CSV')
    analysis_parser.add_argument('--reference_lap', type=str, required=True, help='Path to reference telemetry CSV')
    analysis_parser.add_argument('--lap_summary', type=str, help='Path to lap summary CSV')
    
    # Visualization command
    viz_parser = subparsers.add_parser('visualize', help='Run visualization only')
    viz_parser.add_argument('--telemetry', type=str, required=True, help='Path to telemetry CSV')
    viz_parser.add_argument('--reference', type=str, help='Path to reference telemetry CSV')
    viz_parser.add_argument('--output', type=str, default='reports/track_animation.mp4', help='Output path')
    viz_parser.add_argument('--static', action='store_true', help='Create static track map')
    viz_parser.add_argument('--comparison', action='store_true', help='Create comparison plot')
    viz_parser.add_argument('--color_by', type=str, choices=['speed', 'brake', 'throttle'], help='Color coding')
    viz_parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate AI report only')
    report_parser.add_argument('--corner_data', type=str, required=True, help='Path to corner analysis CSV')
    report_parser.add_argument('--consistency', type=str, help='Path to consistency stats JSON')
    report_parser.add_argument('--driver', type=str, required=True, help='Driver code')
    report_parser.add_argument('--gp', type=str, required=True, help='Grand Prix name')
    report_parser.add_argument('--year', type=int, required=True, help='Year')
    report_parser.add_argument('--output', type=str, default='reports/performance_report.md', help='Output path')
    report_parser.add_argument('--api_key', type=str, help='Anthropic API key')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Execute the appropriate command
    if args.command == 'complete':
        run_complete_workflow(args)
    elif args.command == 'pipeline':
        run_pipeline(args)
    elif args.command == 'analyze':
        run_analysis(args)
    elif args.command == 'visualize':
        run_visualization(args)
    elif args.command == 'report':
        run_report(args)


if __name__ == "__main__":
    main()