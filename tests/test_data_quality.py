from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_quality import build_quality_report


def test_duplicate_grain_is_critical() -> None:
    row = {
        "project_key": "p1",
        "snapshot_date": pd.Timestamp("2025-01-01"),
        "site_name": "Example",
        "technology": "Solar",
        "stage": "Planning",
        "capacity_mw": 10.0,
    }
    report = build_quality_report(pd.DataFrame([row, row]))
    assert report["duplicate_snapshot_project_rows"] == 1
    assert any(
        issue["severity"] == "critical"
        and issue["check"] == "snapshot_project_uniqueness"
        for issue in report["issues"]
    )


def test_packaged_panel_has_unique_snapshot_project_grain() -> None:
    path = Path("data/processed/repd_panel.csv.gz")
    panel = pd.read_csv(path, compression="gzip", low_memory=False)
    report = build_quality_report(panel)
    assert report["duplicate_snapshot_project_rows"] == 0
    assert report["projects"] > 1_000
    assert report["snapshots"] >= 8
