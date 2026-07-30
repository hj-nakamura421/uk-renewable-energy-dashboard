from __future__ import annotations

import argparse
from pathlib import Path

from src.data_quality import write_quality_report
from src.external_factors import refresh_external_context
from src.model import load_panel, train_all
from src.repd_clean import build_panel
from src.repd_download import download_historical_repd

RAW_DIR = Path("data/raw/repd")
PANEL_PATH = Path("data/processed/repd_panel.csv.gz")
FORECAST_PATH = Path("data/processed/latest_forecasts.csv.gz")
METRICS_PATH = Path("data/processed/model_metrics.json")
QUALITY_PATH = Path("data/processed/data_quality_report.json")
EXTERNAL_CONTEXT_PATH = Path("data/processed/external_context.csv")
EXTERNAL_METADATA_PATH = Path("data/processed/external_metadata.json")
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
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Keep the existing official macro context file instead of refreshing it.",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not args.skip_download:
        print("\n1/4 Downloading historical official REPD snapshots...")
        records = download_historical_repd(
            RAW_DIR,
            start_year=args.start_year,
            frequency=args.frequency,
        )
        print(f"Downloader obtained {len(records)} unique files.")
    else:
        print("\n1/4 Skipping download and using local raw files.")

    print("\n2/4 Cleaning, linking and quality-checking project snapshots...")
    raw_files = [
        path
        for path in RAW_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls"}
    ]
    if args.skip_download and not raw_files and PANEL_PATH.exists():
        print(f"No raw files found; reusing the packaged panel at {PANEL_PATH}.")
        panel = load_panel(PANEL_PATH)
    else:
        panel = build_panel(RAW_DIR, PANEL_PATH)
    quality = write_quality_report(panel, QUALITY_PATH)
    print(
        f"Data quality: {quality['rows']:,} rows, {quality['projects']:,} projects, "
        f"{quality['snapshots']} snapshots, status={quality['readiness']}."
    )
    if panel["snapshot_date"].nunique() < 8:
        raise RuntimeError(
            "Only a small number of snapshots were found. Add more official historical REPD files "
            "to data/raw/repd before treating forecasts as credible."
        )

    print("\n3/4 Refreshing official UK economic context...")
    if args.skip_external and EXTERNAL_CONTEXT_PATH.exists():
        print(f"Keeping {EXTERNAL_CONTEXT_PATH}.")
    else:
        try:
            external = refresh_external_context(
                EXTERNAL_CONTEXT_PATH,
                EXTERNAL_METADATA_PATH,
            )
            print(f"Saved {len(external):,} monthly macro observations.")
        except Exception as exc:  # noqa: BLE001
            if EXTERNAL_CONTEXT_PATH.exists():
                print(f"External refresh failed; retaining the previous file: {exc}")
            else:
                raise RuntimeError(
                    "Official external data could not be downloaded and no cached "
                    f"context exists: {exc}"
                ) from exc

    print("\n4/4 Training leakage-aware survival and CatBoost models...")
    report = train_all(PANEL_PATH, MODEL_DIR, FORECAST_PATH, METRICS_PATH)
    print(
        f"Selected {report['selected_model']} with release status "
        f"{report['release_status']}."
    )

    print("\nSetup complete. Start the platform with:\n")
    print("    streamlit run app.py")
    print("\nCommit data/processed and models for deployment; raw files remain ignored by Git.")


if __name__ == "__main__":
    main()
