# F1 Telemetry AI Performance Coach

A comprehensive system that pulls real F1 telemetry data, renders animated visualizations of car performance on track, and uses AI to generate detailed driver performance reports with actionable coaching insights.

## 🎯 Project Overview

This system analyzes Formula 1 telemetry data to help drivers understand their performance and identify areas for improvement. It combines data science, visualization, and AI to provide race-engineer level analysis.

### Key Features

- **Real F1 Data**: Pulls official telemetry data from 2018+ seasons using FastF1
- **Corner Analysis**: Detects corners and computes performance deltas (brake points, apex speeds, time loss)
- **Track Visualization**: Animated 2D track maps with color-coded telemetry data
- **AI Coaching**: Uses Claude API to generate detailed performance reports with actionable insights
- **Consistency Analysis**: Identifies lap-to-lap consistency issues

## 🏗️ Architecture

The system consists of 4 main modules:

### 1. Data Pipeline (`f1_pipeline.py`)
- Pulls session, lap, and telemetry data using FastF1
- Outputs: `fastest_lap.csv`, `all_laps.csv`, `lap_summary.csv`

### 2. Corner-Delta Engine (`corner_analysis.py`)
- Detects corners using speed trace analysis
- Computes performance deltas between driver and reference laps
- Analyzes lap-to-lap consistency
- Outputs: `corner_analysis.csv`, `consistency_stats.json`

### 3. Visualization (`track_animation.py`)
- Creates animated track visualizations
- Color-codes by speed, braking, or throttle
- Supports comparison plots between laps
- Outputs: MP4 animations, PNG comparison plots

### 4. AI Coaching Layer (`generate_report.py`)
- Uses Claude API with race-engineer persona
- Generates detailed performance reports
- Provides actionable recommendations based on telemetry data
- Outputs: Markdown performance reports

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run complete analysis workflow
python f1_coach.py complete --year 2024 --gp "Monza" --session R --driver VER --reference PER
```

This will:
1. Pull telemetry data for VER and PER from 2024 Monza race
2. Analyze corner-by-corner performance differences
3. Create animated track visualizations
4. Generate an AI-powered performance report

### Individual Module Usage

```bash
# Data pipeline only
python f1_coach.py pipeline --year 2024 --gp "Monza" --session R --driver VER

# Corner analysis only
python f1_coach.py analyze --driver_lap data/VER_Monza_2024_fastest_lap.csv --reference_lap data/PER_Monza_2024_fastest_lap.csv

# Visualization only
python f1_coach.py visualize --telemetry data/VER_Monza_2024_fastest_lap.csv --output reports/animation.mp4

# AI report only
python f1_coach.py report --corner_data data/corner_analysis.csv --driver VER --gp "Monza" --year 2024
```

## 📁 Project Structure

```
f1-ai-performance-coach/
├── f1_coach.py              # Main CLI interface
├── f1_pipeline.py          # Data pipeline module
├── corner_analysis.py      # Corner-delta engine
├── track_animation.py      # Visualization module
├── generate_report.py      # AI coaching layer
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Output data directory
│   ├── *_fastest_lap.csv
│   ├── *_all_laps.csv
│   ├── *_lap_summary.csv
│   ├── corner_analysis.csv
│   └── consistency_stats.json
├── reports/              # Generated reports and visualizations
│   ├── *_track_animation.mp4
│   ├── *_comparison.png
│   └── *_performance_report.md
└── f1_cache/             # FastF1 cache directory
```

## 🔧 Configuration

### API Key Setup

Set your Hugging Face API key for AI report generation:

```bash
# Set as environment variable (Linux/Mac)
export HUGGINGFACE_API_KEY=your_api_key_here

# Set as environment variable (Windows)
set HUGGINGFACE_API_KEY=your_api_key_here

# Or pass it directly
python f1_coach.py report --api_key your_api_key_here ...
```

Get your free API key from: https://huggingface.co/settings/tokens

### Session Types

- `FP1`, `FP2`, `FP3` - Practice sessions
- `Q` - Qualifying
- `R` - Race (default)
- `S` - Sprint race

### Driver Codes

Use official 3-letter F1 driver codes (e.g., VER, HAM, LEC, NOR, PER, etc.)

## 📊 Output Examples

### Corner Analysis
The system provides detailed corner-by-corner analysis:
- Brake point deltas (meters)
- Minimum speed deltas (km/h)
- Time loss through corners (seconds)
- Throttle, brake, and gear data at entry/apex/exit

### AI Report Structure
Generated reports include:
1. **Session Summary** - Overall performance assessment
2. **Time Loss Breakdown** - Ranked corners by time impact
3. **Root Causes** - Technical analysis with telemetry evidence
4. **What to Work On** - Actionable recommendations
5. **Consistency Issues** - Lap-to-lap variability analysis

## 🎨 Visualization Options

### Animated Track
```bash
python f1_coach.py visualize --telemetry data/VER_Monza_2024_fastest_lap.csv --color_by speed
```

Color options:
- `speed` - Color by speed (default)
- `brake` - Color by braking intensity
- `throttle` - Color by throttle position

### Comparison Plot
```bash
python f1_coach.py visualize --telemetry data/VER_Monza_2024_fastest_lap.csv --reference data/PER_Monza_2024_fastest_lap.csv --comparison
```

### Static Track Map
```bash
python f1_coach.py visualize --telemetry data/VER_Monza_2024_fastest_lap.csv --static
```

## 🔍 Technical Details

### Corner Detection Algorithm
- Uses scipy signal processing to detect speed minima
- Identifies corner entry, apex, and exit points
- Filters by minimum speed drop and duration

### Performance Metrics
- **Brake Point Delta**: Distance difference in braking points
- **Min Speed Delta**: Speed difference at corner apex
- **Corner Time Delta**: Time difference through corner
- **Consistency**: Standard deviation of lap and sector times

### Data Sources
- Official F1 telemetry data via FastF1
- Includes: Speed, Throttle, Brake, Gear, RPM, DRS, GPS position
- Data cached locally for faster repeat analysis

## 🛠️ Development

### Adding New Features
The modular architecture makes it easy to extend:
- Add new analysis metrics to `corner_analysis.py`
- Enhance visualizations in `track_animation.py`
- Modify AI prompts in `generate_report.py`

### Testing
Test with different sessions and drivers:
```bash
# Test with qualifying data
python f1_coach.py complete --year 2024 --gp "Monza" --session Q --driver VER --reference PER

# Test with different track
python f1_coach.py complete --year 2024 --gp "Silverstone" --session R --driver HAM --reference NOR
```

## 📝 Requirements

- Python 3.8+
- FastF1 (for F1 data)
- Pandas, NumPy (data processing)
- SciPy (signal processing)
- Matplotlib (visualization)
- Anthropic SDK (AI reports)
- FFmpeg (for video output, optional)

## 🤝 Contributing

This is a project for F1 telemetry analysis and driver coaching. Suggestions and improvements are welcome!

## 📄 License

This project is for educational and analysis purposes. F1 telemetry data is subject to the terms of service of the data providers.

## 🎯 Future Enhancements

- [ ] Web interface for interactive analysis
- [ ] Real-time telemetry analysis
- [ ] Historical performance tracking
- [ ] Team comparison tools
- [ ] Predictive performance modeling
- [ ] Support for multiple seasons comparison

## 📞 Support

For issues or questions about the F1 data, refer to the [FastF1 documentation](https://docs.fastf1.dev/).

For AI-related questions, refer to the [Anthropic API documentation](https://docs.anthropic.com/).

---

**Note**: This system uses official F1 telemetry data and AI analysis to provide coaching insights. Always cross-reference with professional coaching for actual driver development.