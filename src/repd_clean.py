from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

CANONICAL_ALIASES: dict[str, tuple[str, ...]] = {
    "ref_id": ("ref id", "reference id", "repd ref id"),
    "old_ref_id": ("old ref id", "old reference id"),
    "new_application_ref": ("are they re applying new repd ref id", "new repd ref"),
    "old_application_ref": ("are they re applying old repd ref id", "old repd ref"),
    "record_last_updated": ("record last updated dd mm yyyy", "record last updated"),
    "operator": ("operator or applicant", "operator", "applicant"),
    "site_name": ("site name", "project name", "scheme name"),
    "technology": ("technology type", "technology"),
    "capacity_mw": ("installed capacity mwelec", "installed capacity mw", "capacity mw"),
    "status": ("development status",),
    "status_short": ("development status short", "status short"),
    "region": ("region",),
    "country": ("country",),
    "county": ("county",),
    "planning_authority": ("planning authority",),
    "planning_reference": ("planning application reference", "planning reference"),
    "planning_submitted": ("planning application submitted",),
    "planning_granted": ("planning permission granted",),
    "under_construction_date": ("under construction",),
    "operational_date": ("operational",),
    "x_coordinate": ("x coordinate", "x-coordinate", "easting"),
    "y_coordinate": ("y coordinate", "y-coordinate", "northing"),
    "cfd_round": ("cfd allocation round",),
    "cfd_capacity_mw": ("cfd capacity mw",),
}


def normalise_name(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


ALIAS_LOOKUP = {
    normalise_name(alias): canonical
    for canonical, aliases in CANONICAL_ALIASES.items()
    for alias in aliases
}


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, value: str) -> str:
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        self.parent[max(left_root, right_root)] = min(left_root, right_root)


def _detect_header_row(path: Path, sheet_name: str | int = 0) -> int:
    preview = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=25)
    for row_index, row in preview.iterrows():
        values = {normalise_name(value) for value in row.dropna().tolist()}
        if "ref id" in values or ("site name" in values and "technology type" in values):
            return int(row_index)
    return 0


def _best_excel_sheet(path: Path) -> str | int:
    workbook = pd.ExcelFile(path)
    best_sheet: str | int = workbook.sheet_names[0]
    best_score = -1
    for sheet in workbook.sheet_names[:8]:
        try:
            preview = pd.read_excel(path, sheet_name=sheet, header=None, nrows=15)
            text = " ".join(normalise_name(value) for value in preview.astype(str).values.ravel())
            score = text.count("site name") * 4 + text.count("ref id") * 5 + text.count("technology")
            if "summary" in normalise_name(sheet):
                score -= 5
            if score > best_score:
                best_score = score
                best_sheet = sheet
        except Exception:  # noqa: BLE001
            continue
    return best_sheet


def read_snapshot(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
            try:
                frame = pd.read_csv(path, encoding=encoding, low_memory=False)
                if len(frame.columns) > 5:
                    return frame
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode {path}")

    if suffix in {".xlsx", ".xls"}:
        sheet = _best_excel_sheet(path)
        header_row = _detect_header_row(path, sheet)
        return pd.read_excel(path, sheet_name=sheet, header=header_row)

    raise ValueError(f"Unsupported file type: {path}")


def _snapshot_date_from_path(path: Path) -> pd.Timestamp:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if match:
        return pd.Timestamp(match.group(1))
    return pd.Timestamp(path.stat().st_mtime, unit="s").normalize()


def _canonicalise_columns(frame: pd.DataFrame) -> pd.DataFrame:
    rename: dict[object, str] = {}
    used: set[str] = set()
    for column in frame.columns:
        key = normalise_name(column)
        canonical = ALIAS_LOOKUP.get(key)
        if canonical and canonical not in used:
            rename[column] = canonical
            used.add(canonical)
    return frame.rename(columns=rename)


def _extract_reference(value: object) -> str | None:
    if pd.isna(value):
        return None
    match = re.search(r"\d+", str(value))
    return match.group(0) if match else None


def _clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().replace({"nan": "", "None": ""})


def _parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def classify_stage(row: pd.Series) -> str:
    status = normalise_name(f"{row.get('status', '')} {row.get('status_short', '')}")
    if "decommission" in status:
        return "Decommissioned"
    if any(word in status for word in ("abandon", "refus", "withdraw", "expired")):
        return "Stopped"
    if "operational" in status or pd.notna(row.get("operational_date")):
        return "Operational"
    if "construction" in status or pd.notna(row.get("under_construction_date")):
        return "Under Construction"
    if "awaiting construction" in status or "permission granted" in status or pd.notna(row.get("planning_granted")):
        return "Consented"
    if any(word in status for word in ("planning", "application submitted", "appeal")):
        return "Planning"
    if any(word in status for word in ("inception", "pre planning")):
        return "Inception"
    return "Other"


def _fallback_key(row: pd.Series) -> str:
    name = normalise_name(row.get("site_name", "unknown"))[:80]
    authority = normalise_name(row.get("planning_authority", ""))[:40]
    capacity = pd.to_numeric(row.get("capacity_mw"), errors="coerce")
    rounded_capacity = "na" if pd.isna(capacity) else str(round(float(capacity), 1))
    return f"fallback::{name}::{authority}::{rounded_capacity}"


def clean_file(path: Path) -> pd.DataFrame:
    frame = _canonicalise_columns(read_snapshot(path))
    snapshot_date = _snapshot_date_from_path(path)

    required_defaults = {
        "ref_id": "",
        "old_ref_id": "",
        "new_application_ref": "",
        "old_application_ref": "",
        "operator": "",
        "site_name": "",
        "technology": "Unknown",
        "capacity_mw": np.nan,
        "status": "",
        "status_short": "",
        "region": "Unknown",
        "country": "Unknown",
        "county": "",
        "planning_authority": "",
        "planning_reference": "",
        "planning_submitted": pd.NaT,
        "planning_granted": pd.NaT,
        "under_construction_date": pd.NaT,
        "operational_date": pd.NaT,
        "x_coordinate": np.nan,
        "y_coordinate": np.nan,
        "cfd_round": "",
        "cfd_capacity_mw": np.nan,
    }
    for column, default in required_defaults.items():
        if column not in frame.columns:
            frame[column] = default

    for column in (
        "ref_id", "old_ref_id", "new_application_ref", "old_application_ref",
        "operator", "site_name", "technology", "status", "status_short",
        "region", "country", "county", "planning_authority", "planning_reference",
        "cfd_round",
    ):
        frame[column] = _clean_text(frame[column])

    for column in ("capacity_mw", "x_coordinate", "y_coordinate", "cfd_capacity_mw"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    for column in (
        "planning_submitted", "planning_granted", "under_construction_date", "operational_date"
    ):
        frame[column] = _parse_date(frame[column])

    frame["snapshot_date"] = snapshot_date
    frame["source_file"] = path.name
    frame["stage"] = frame.apply(classify_stage, axis=1)
    frame = frame[frame["site_name"].ne("") | frame["ref_id"].ne("")].copy()
    return frame[list(required_defaults) + ["snapshot_date", "source_file", "stage"]]


def assign_stable_project_keys(panel: pd.DataFrame) -> pd.DataFrame:
    union_find = UnionFind()
    for row in panel.itertuples(index=False):
        current = _extract_reference(getattr(row, "ref_id", ""))
        linked_values = (
            getattr(row, "old_ref_id", ""),
            getattr(row, "new_application_ref", ""),
            getattr(row, "old_application_ref", ""),
        )
        if current:
            union_find.find(current)
            for linked_value in linked_values:
                linked = _extract_reference(linked_value)
                if linked:
                    union_find.union(current, linked)

    keys: list[str] = []
    for _, row in panel.iterrows():
        current = _extract_reference(row.get("ref_id"))
        if current:
            keys.append(f"repd::{union_find.find(current)}")
        else:
            keys.append(_fallback_key(row))
    panel = panel.copy()
    panel["project_key"] = keys
    return panel


def add_coordinates(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    panel["longitude"] = np.nan
    panel["latitude"] = np.nan
    valid = panel["x_coordinate"].between(0, 800_000) & panel["y_coordinate"].between(0, 1_400_000)
    if valid.any():
        transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
        longitude, latitude = transformer.transform(
            panel.loc[valid, "x_coordinate"].to_numpy(),
            panel.loc[valid, "y_coordinate"].to_numpy(),
        )
        panel.loc[valid, "longitude"] = longitude
        panel.loc[valid, "latitude"] = latitude
    return panel


def build_panel(raw_dir: Path, output_path: Path) -> pd.DataFrame:
    files = sorted(
        path for path in raw_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls"}
    )
    if not files:
        raise FileNotFoundError(
            f"No REPD files found in {raw_dir}. Run the downloader or add official files manually."
        )

    frames: list[pd.DataFrame] = []
    failures: defaultdict[str, str] = defaultdict(str)
    for index, path in enumerate(files, start=1):
        try:
            frame = clean_file(path)
            frames.append(frame)
            print(f"[{index}/{len(files)}] Cleaned {path.name}: {len(frame):,} rows")
        except Exception as exc:  # noqa: BLE001
            failures[path.name] = str(exc)
            print(f"[{index}/{len(files)}] Failed {path.name}: {exc}")

    if len(frames) < 2:
        raise RuntimeError(
            "Fewer than two snapshots could be cleaned. Historical forecasting requires multiple snapshots. "
            f"Failures: {dict(failures)}"
        )

    panel = pd.concat(frames, ignore_index=True)
    panel = assign_stable_project_keys(panel)
    panel = add_coordinates(panel)
    panel = panel.sort_values(["snapshot_date", "project_key"]).drop_duplicates(
        ["snapshot_date", "project_key"], keep="last"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output_path, index=False, compression="gzip")
    print(
        f"Saved panel with {len(panel):,} rows, {panel['project_key'].nunique():,} projects "
        f"and {panel['snapshot_date'].nunique():,} snapshots to {output_path}"
    )
    return panel


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean historical REPD snapshots into a panel.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/repd"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/repd_panel.csv.gz"),
    )
    args = parser.parse_args()
    build_panel(args.raw_dir, args.output)


if __name__ == "__main__":
    main()
