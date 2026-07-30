from __future__ import annotations

import argparse
from pathlib import Path

from src.model import train_all
from src.repd_clean import build_panel
from src.repd_download import download_historical_repd

RAW_DIR = Path("data/raw/repd")
PANEL_PATH = Path("data/processed/repd_panel.csv.gz")
FORECAST_PATH = Path("data/processed/latest_forecasts.csv.gz")
METRICS_PATH = Path("data/processed/model_metrics.json")
MODEL_DIR = Path("models")


def main() -> None:
    parser = argparse.ArgumentParser(description="One-command forecasting platform setup.")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Use REPD files already placed in data/raw/repd.",
    )
    parser.add_argument("--start-year", type=int, default=2014)
    parser.add_argument("--frequency", choices=["quarterly", "monthly"], default="quarterly")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not args.skip_download:
        print("\n1/3 Downloading historical official REPD snapshots...")
        records = download_historical_repd(
            RAW_DIR,
            start_year=args.start_year,
            frequency=args.frequency,
        )
        print(f"Downloader obtained {len(records)} unique files.")
    else:
        print("\n1/3 Skipping download and using local raw files.")

    print("\n2/3 Cleaning and linking project snapshots...")
    panel = build_panel(RAW_DIR, PANEL_PATH)
    if panel["snapshot_date"].nunique() < 8:
        raise RuntimeError(
            "Only a small number of snapshots were found. Add more official historical REPD files "
            "to data/raw/repd before treating forecasts as credible."
        )

    print("\n3/3 Training time-based 2-, 3- and 5-year models...")
    train_all(PANEL_PATH, MODEL_DIR, FORECAST_PATH, METRICS_PATH)

    print("\nSetup complete. Start the platform with:\n")
    print("    streamlit run app.py")
    print("\nCommit data/processed and models for deployment; raw files remain ignored by Git.")


if __name__ == "__main__":
    main()
