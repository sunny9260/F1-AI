"""
AI Coaching Layer
Generates performance reports using Claude API based on corner analysis and consistency data.
Acts as a race engineer to provide actionable feedback.

Usage:
    python generate_report.py --corner_data data/corner_analysis.csv --consistency data/consistency_stats.json --driver VER --gp Monza --year 2024
"""

import argparse
import json
import pandas as pd
from typing import Dict, Optional
import os


def load_corner_analysis(corner_data_path: str) -> pd.DataFrame:
    """Load corner analysis data from CSV."""
    return pd.read_csv(corner_data_path)


def load_consistency_stats(consistency_path: str) -> Dict:
    """Load consistency statistics from JSON."""
    with open(consistency_path, 'r') as f:
        return json.load(f)


def create_race_engineer_prompt(driver: str, gp: str, year: int, 
                                corner_data: pd.DataFrame,
                                consistency_stats: Optional[Dict] = None) -> str:
    """
    Create a detailed prompt for Claude API with race engineer persona.
    
    Args:
        driver: Driver code (e.g., 'VER')
        gp: Grand Prix name (e.g., 'Monza')
        year: Year of the session
        corner_data: DataFrame with corner analysis results
        consistency_stats: Optional consistency statistics dictionary
    
    Returns:
        Formatted prompt string for Claude API
    """
    
    # Identify top time loss corners
    top_loss_corners = corner_data.nlargest(5, 'time_loss_rank')
    
    # Format corner data for the prompt
    corner_summary = "CORNER ANALYSIS (Top 5 Time Loss Areas):\n\n"
    for _, corner in top_loss_corners.iterrows():
        corner_summary += f"Corner {corner['corner_number']}:\n"
        corner_summary += f"  - Time Delta: {corner['corner_time_delta_s']:+.3f}s\n"
        corner_summary += f"  - Brake Point Delta: {corner['brake_point_delta_m']:+.1f}m "
        corner_summary += f"({'Later' if corner['brake_point_delta_m'] > 0 else 'Earlier'} than reference)\n"
        corner_summary += f"  - Min Speed Delta: {corner['min_speed_delta_kmh']:+.1f} km/h "
        corner_summary += f"({'Slower' if corner['min_speed_delta_kmh'] < 0 else 'Faster'} than reference)\n"
        corner_summary += f"  - Driver Entry Speed: {corner['driver_entry_speed']:.1f} km/h\n"
        corner_summary += f"  - Driver Apex Speed: {corner['driver_apex_speed']:.1f} km/h\n"
        corner_summary += f"  - Driver Exit Speed: {corner['driver_exit_speed']:.1f} km/h\n"
        corner_summary += f"  - Reference Entry Speed: {corner['ref_entry_speed']:.1f} km/h\n"
        corner_summary += f"  - Reference Apex Speed: {corner['ref_apex_speed']:.1f} km/h\n"
        corner_summary += f"  - Reference Exit Speed: {corner['ref_exit_speed']:.1f} km/h\n"
        corner_summary += f"  - Entry Throttle: {corner['entry_throttle']:.1f}%\n"
        corner_summary += f"  - Apex Throttle: {corner['apex_throttle']:.1f}%\n"
        corner_summary += f"  - Entry Brake: {corner['entry_brake']:.0f}\n"
        corner_summary += f"  - Apex Brake: {corner['apex_brake']:.0f}\n"
        corner_summary += f"  - Entry Gear: {corner['entry_gear']:.0f}\n"
        corner_summary += f"  - Apex Gear: {corner['apex_gear']:.0f}\n\n"
    
    # Add consistency analysis if available
    consistency_section = ""
    if consistency_stats:
        consistency_section = "\nLAP CONSISTENCY ANALYSIS:\n\n"
        consistency_section += f"Total Laps Analyzed: {consistency_stats['total_laps']}\n"
        consistency_section += f"Lap Time Mean: {consistency_stats['lap_time_mean_s']:.3f}s\n"
        consistency_section += f"Lap Time Std Dev: {consistency_stats['lap_time_std_s']:.3f}s\n"
        consistency_section += f"Sector 1 Mean: {consistency_stats['sector1_mean_s']:.3f}s (Std: {consistency_stats['sector1_std_s']:.3f}s)\n"
        consistency_section += f"Sector 2 Mean: {consistency_stats['sector2_mean_s']:.3f}s (Std: {consistency_stats['sector2_std_s']:.3f}s)\n"
        consistency_section += f"Sector 3 Mean: {consistency_stats['sector3_mean_s']:.3f}s (Std: {consistency_stats['sector3_std_s']:.3f}s)\n"
        consistency_section += f"Most Variable Sector: {consistency_stats['most_variable_sector']}\n\n"
    
    # Calculate total time loss
    total_time_loss = corner_data['corner_time_delta_s'].sum()
    
    prompt = f"""You are an expert F1 race engineer analyzing telemetry data for driver {driver} at the {year} {gp} Grand Prix.

TOTAL TIME LOSS: {total_time_loss:+.3f}s compared to reference lap

{corner_summary}

{consistency_section}

INSTRUCTIONS:
Provide a technical, data-driven performance report with the following sections:

1. **SESSION SUMMARY** (2-3 sentences)
   - Overall performance assessment
   - Key takeaway from the data

2. **TIME LOSS BREAKDOWN** (Ranked by impact)
   - List the top 3 corners where time is being lost
   - For each corner, specify the exact time loss and primary cause
   - Use the telemetry data to support your analysis

3. **ROOT CAUSES** (Technical analysis)
   - For each major issue, identify the specific telemetry evidence
   - Reference brake points, apex speeds, throttle application, gear choices
   - Explain WHY the time loss is occurring based on the data

4. **WHAT TO WORK ON** (Actionable recommendations)
   - Provide 2-3 concrete, specific improvements
   - Each recommendation should be directly tied to the telemetry data
   - Include specific techniques or adjustments (e.g., "brake 10m later at Turn 7", "maintain 5km/h higher apex speed through Turn 12")

5. **CONSISTENCY ISSUES** (If applicable)
   - Highlight any consistency problems from the lap data
   - Suggest specific approaches to improve consistency

Keep the tone professional, precise, and focused on actionable insights. Avoid fluff or general advice - every recommendation should be backed by the provided telemetry data."""

    return prompt


def generate_huggingface_report(prompt: str, api_key: Optional[str] = None, model: str = "mistralai/Mistral-7B-Instruct-v0.2") -> str:
    """
    Generate report using Hugging Face Inference API.
    
    Args:
        prompt: The formatted prompt for the AI model
        api_key: Optional Hugging Face API key (if None, will try to get from environment)
        model: Hugging Face model to use
    
    Returns:
        Generated report text
    """
    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        print("Error: huggingface_hub package not installed. Install with: pip install huggingface_hub")
        return None
    
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.environ.get('HUGGINGFACE_API_KEY')
    
    if not api_key:
        print("Warning: HUGGINGFACE_API_KEY not found. Generating sample report without AI...")
        return generate_sample_report(prompt)
    
    try:
        client = InferenceClient(token=api_key)
        
        # Format prompt for Mistral model
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        
        response = client.text_generation(
            formatted_prompt,
            model=model,
            max_new_tokens=4096,
            temperature=0.3,
            do_sample=True,
        )
        
        return response
    
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        print("Generating sample report without AI...")
        return generate_sample_report(prompt)


def generate_sample_report(prompt: str) -> str:
    """
    Generate a sample report when AI API is not available.
    This provides a template showing what the AI report would look like.
    """
    return """# F1 Performance Report - Sample

**Note**: This is a sample report generated without AI analysis. To get detailed AI-powered insights, set up your Hugging Face API key.

## Session Summary
This sample report demonstrates the structure of the AI-generated performance analysis. The actual AI report would provide detailed insights based on the corner analysis and consistency data.

## Time Loss Breakdown
The AI would analyze the corner data to identify the top 3 corners where time is being lost, with specific time deltas and primary causes based on the telemetry evidence.

## Root Causes
For each major issue, the AI would identify specific telemetry evidence from the corner analysis data, including:
- Brake point analysis
- Apex speed comparisons  
- Throttle application patterns
- Gear selection analysis

## What to Work On
The AI would provide 2-3 concrete, specific improvements directly tied to the telemetry data, such as:
- Specific braking point adjustments at particular corners
- Apex speed targets based on reference lap data
- Throttle application techniques for corner exit

## Consistency Issues
If consistency data is available, the AI would highlight lap-to-lap variability issues and suggest specific approaches to improve consistency.

---

**To enable AI-powered reports**: Set your HUGGINGFACE_API_KEY environment variable or pass it as --api_key parameter when running the report command."""


def save_report(report: str, output_path: str) -> None:
    """Save the generated report to a markdown file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Report saved to {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corner_data", type=str, required=True, help="Path to corner analysis CSV")
    parser.add_argument("--consistency", type=str, help="Path to consistency stats JSON")
    parser.add_argument("--driver", type=str, required=True, help="Driver code (e.g., VER)")
    parser.add_argument("--gp", type=str, required=True, help="Grand Prix name (e.g., Monza)")
    parser.add_argument("--year", type=int, required=True, help="Year of the session")
    parser.add_argument("--output", type=str, default="reports/performance_report.md", help="Output report path")
    parser.add_argument("--api_key", type=str, help="Hugging Face API key (or set HUGGINGFACE_API_KEY env var)")
    parser.add_argument("--model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2", help="Hugging Face model to use")
    args = parser.parse_args()
    
    # Load data
    print(f"Loading corner analysis from {args.corner_data}...")
    corner_data = load_corner_analysis(args.corner_data)
    
    consistency_stats = None
    if args.consistency:
        print(f"Loading consistency stats from {args.consistency}...")
        consistency_stats = load_consistency_stats(args.consistency)
    
    # Create prompt
    print("Creating race engineer prompt...")
    prompt = create_race_engineer_prompt(
        args.driver, args.gp, args.year, corner_data, consistency_stats
    )
    
    # Generate report
    print("Generating performance report...")
    report = generate_huggingface_report(prompt, args.api_key)
    
    if report:
        # Create output directory if needed
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        
        # Save report
        save_report(report, args.output)
        print("\n" + "="*50)
        print("PERFORMANCE REPORT GENERATED SUCCESSFULLY")
        print("="*50)
        print(f"\nDriver: {args.driver}")
        print(f"Session: {args.year} {args.gp}")
        print(f"Report saved to: {args.output}")
    else:
        print("Failed to generate report. Please check your API key and connection.")


if __name__ == "__main__":
    main()