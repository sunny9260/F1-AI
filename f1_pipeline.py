"""
F1 Telemetry Data Pipeline
Pulls session + lap + telemetry data for a driver using FastF1, cleans it,
and exports a per-lap telemetry CSV ready for visualization / AI analysis.

Usage:
    python f1_pipeline.py --year 2024 --gp "Monza" --session R --driver VER
"""

import argparse
import os
import fastf1
import pandas as pd

# FastF1 caches raw API responses locally so repeat runs are fast/offline.
CACHE_DIR = "f1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)


def load_session(year: int, gp: str, session_type: str):
    """session_type: 'FP1'/'FP2'/'FP3'/'Q'/'R'/'S' (sprint)"""
    session = fastf1.get_session(year, gp, session_type)
    session.load()  # downloads laps + telemetry + weather
    return session


def get_driver_laps(session, driver_code: str) -> pd.DataFrame:
    laps = session.laps.pick_drivers(driver_code)
    if laps.empty:
        raise ValueError(f"No laps found for driver '{driver_code}' in this session.")
    return laps


def get_fastest_lap_telemetry(laps: pd.DataFrame) -> pd.DataFrame:
    fastest = laps.pick_fastest()
    tel = fastest.get_telemetry()
    # Keep the columns that matter for visualization + analysis
    cols = ["Time", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS"]
    tel = tel[[c for c in cols if c in tel.columns]].copy()
    tel["LapNumber"] = fastest["LapNumber"]
    tel["LapTime"] = fastest["LapTime"]
    return tel


def get_all_laps_telemetry(session, laps: pd.DataFrame) -> pd.DataFrame:
    """Telemetry for every completed lap (for consistency/variance analysis)."""
    all_tel = []
    for _, lap in laps.iterrows():
        try:
            tel = lap.get_telemetry()
        except Exception:
            continue
        cols = ["Time", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS"]
        tel = tel[[c for c in cols if c in tel.columns]].copy()
        tel["LapNumber"] = lap["LapNumber"]
        tel["LapTime"] = lap["LapTime"]
        all_tel.append(tel)
    return pd.concat(all_tel, ignore_index=True) if all_tel else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--gp", type=str, required=True, help="Grand Prix name, e.g. 'Monza'")
    parser.add_argument("--session", type=str, default="R", help="FP1/FP2/FP3/Q/R/S")
    parser.add_argument("--driver", type=str, required=True, help="3-letter driver code, e.g. VER")
    parser.add_argument("--out", type=str, default="data")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print(f"Loading {args.year} {args.gp} {args.session} ...")
    session = load_session(args.year, args.gp, args.session)

    laps = get_driver_laps(session, args.driver)
    print(f"Found {len(laps)} laps for {args.driver}")

    fastest_tel = get_fastest_lap_telemetry(laps)
    fastest_path = os.path.join(args.out, f"{args.driver}_{args.gp}_{args.year}_fastest_lap.csv")
    fastest_tel.to_csv(fastest_path, index=False)
    print(f"Fastest lap telemetry -> {fastest_path}")

    all_tel = get_all_laps_telemetry(session, laps)
    all_path = os.path.join(args.out, f"{args.driver}_{args.gp}_{args.year}_all_laps.csv")
    all_tel.to_csv(all_path, index=False)
    print(f"All-laps telemetry -> {all_path}")

    # Quick lap-time summary, useful for spotting consistency issues
    summary = laps[["LapNumber", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time", "Compound"]]
    summary_path = os.path.join(args.out, f"{args.driver}_{args.gp}_{args.year}_lap_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Lap summary -> {summary_path}")


if __name__ == "__main__":
    main()