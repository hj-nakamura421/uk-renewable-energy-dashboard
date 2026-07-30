from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = (
    "project_key",
    "snapshot_date",
    "site_name",
    "technology",
    "stage",
    "capacity_mw",
)
ALLOWED_STAGES = {
    "Stopped",
    "Inception",
    "Other",
    "Planning",
    "Consented",
    "Under Construction",
    "Operational",
    "Decommissioned",
}


def build_quality_report(panel: pd.DataFrame) -> dict[str, Any]:
    frame = panel.copy()
    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"], errors="coerce")
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    duplicate_grain = (
        int(frame.duplicated(["snapshot_date", "project_key"]).sum())
        if not missing_columns
        else None
    )
    snapshots = sorted(frame["snapshot_date"].dropna().unique())
    snapshot_counts = (
        frame.groupby("snapshot_date", dropna=False)
        .agg(rows=("project_key", "size"), projects=("project_key", "nunique"))
        .reset_index()
    )
    fallback_keys = (
        frame["project_key"].fillna("").astype(str).str.startswith("fallback::")
        if "project_key" in frame
        else pd.Series(False, index=frame.index)
    )
    invalid_stages = (
        sorted(set(frame["stage"].dropna().astype(str)) - ALLOWED_STAGES)
        if "stage" in frame
        else []
    )
    capacity = pd.to_numeric(frame.get("capacity_mw"), errors="coerce")
    negative_capacity = int(capacity.lt(0).sum())
    future_snapshot_rows = int(
        frame["snapshot_date"].gt(pd.Timestamp.now().normalize()).sum()
    )
    issues: list[dict[str, Any]] = []

    if missing_columns:
        issues.append(
            {
                "severity": "critical",
                "check": "required_columns",
                "evidence": missing_columns,
                "impact": "The forecasting grain cannot be reconstructed.",
            }
        )
    if duplicate_grain:
        issues.append(
            {
                "severity": "critical",
                "check": "snapshot_project_uniqueness",
                "evidence": duplicate_grain,
                "impact": "Duplicate project snapshots can overweight projects and inflate totals.",
            }
        )
    if len(snapshots) < 20:
        issues.append(
            {
                "severity": "high",
                "check": "temporal_coverage",
                "evidence": len(snapshots),
                "impact": (
                    "The number of independent time points is too small to estimate "
                    "macroeconomic effects reliably."
                ),
            }
        )
    if invalid_stages:
        issues.append(
            {
                "severity": "high",
                "check": "stage_domain",
                "evidence": invalid_stages,
                "impact": "Unknown stages can break progression features and comparisons.",
            }
        )
    if negative_capacity:
        issues.append(
            {
                "severity": "high",
                "check": "capacity_validity",
                "evidence": negative_capacity,
                "impact": "Negative capacity is not valid for project or portfolio forecasts.",
            }
        )
    if future_snapshot_rows:
        issues.append(
            {
                "severity": "high",
                "check": "future_snapshot_dates",
                "evidence": future_snapshot_rows,
                "impact": "Future-dated source records can introduce time leakage.",
            }
        )
    if float(fallback_keys.mean()) > 0.05:
        issues.append(
            {
                "severity": "medium",
                "check": "entity_resolution",
                "evidence": round(float(fallback_keys.mean()), 4),
                "impact": (
                    "Projects without stable reference IDs are more vulnerable to false "
                    "matches or split histories."
                ),
            }
        )

    return {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "grain": "one project per REPD source snapshot",
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "projects": int(frame.get("project_key", pd.Series(dtype=str)).nunique()),
        "snapshots": int(len(snapshots)),
        "snapshot_start": str(pd.Timestamp(snapshots[0]).date()) if snapshots else None,
        "snapshot_end": str(pd.Timestamp(snapshots[-1]).date()) if snapshots else None,
        "duplicate_snapshot_project_rows": duplicate_grain,
        "fallback_project_key_rate": round(float(fallback_keys.mean()), 4),
        "negative_capacity_rows": negative_capacity,
        "future_snapshot_rows": future_snapshot_rows,
        "missing_required_columns": missing_columns,
        "invalid_stages": invalid_stages,
        "null_rates": {
            column: round(float(frame[column].isna().mean()), 4)
            for column in REQUIRED_COLUMNS
            if column in frame
        },
        "snapshot_counts": [
            {
                "snapshot_date": str(pd.Timestamp(row.snapshot_date).date()),
                "rows": int(row.rows),
                "projects": int(row.projects),
            }
            for row in snapshot_counts.itertuples(index=False)
            if pd.notna(row.snapshot_date)
        ],
        "issues": issues,
        "readiness": (
            "needs_caveats"
            if any(issue["severity"] in {"critical", "high"} for issue in issues)
            else "ready"
        ),
    }


def write_quality_report(panel: pd.DataFrame, path: Path) -> dict[str, Any]:
    report = build_quality_report(panel)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
