from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

STAGE_RANK = {
    "Stopped": 0,
    "Inception": 1,
    "Other": 1,
    "Planning": 2,
    "Consented": 3,
    "Under Construction": 4,
    "Operational": 5,
    "Decommissioned": 5,
}

NUMERIC_FEATURES = [
    "log_capacity_mw",
    "project_age_years",
    "stage_rank",
    "planning_reference_present",
    "planning_granted_flag",
    "under_construction_flag",
    "data_completeness",
    "cfd_flag",
]
CATEGORICAL_FEATURES = ["technology", "region", "country", "stage"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass
class ModelResult:
    horizon_years: int
    train_rows: int
    test_rows: int
    train_end: str
    test_start: str
    positive_rate_train: float
    positive_rate_test: float
    roc_auc: float | None
    brier_score: float
    accuracy: float
    precision: float
    recall: float


def load_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path, compression="gzip", low_memory=False)
    date_columns = [
        "snapshot_date", "planning_submitted", "planning_granted",
        "under_construction_date", "operational_date",
    ]
    for column in date_columns:
        if column in panel.columns:
            panel[column] = pd.to_datetime(panel[column], errors="coerce")
    return panel


def add_features(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    panel["capacity_mw"] = pd.to_numeric(panel["capacity_mw"], errors="coerce")
    panel["first_seen"] = panel.groupby("project_key")["snapshot_date"].transform("min")
    panel["project_age_years"] = (
        panel["snapshot_date"] - panel["first_seen"]
    ).dt.days.div(365.25).clip(lower=0)
    panel["log_capacity_mw"] = np.log1p(panel["capacity_mw"].clip(lower=0))
    panel["stage_rank"] = panel["stage"].map(STAGE_RANK).fillna(1)
    panel["planning_reference_present"] = panel["planning_reference"].fillna("").astype(str).str.strip().ne("").astype(int)
    panel["planning_granted_flag"] = (
        panel["stage"].isin(["Consented", "Under Construction", "Operational"])
        | panel["planning_granted"].notna()
    ).astype(int)
    panel["under_construction_flag"] = (
        panel["stage"].isin(["Under Construction", "Operational"])
        | panel["under_construction_date"].notna()
    ).astype(int)
    completeness_columns = [
        "operator", "site_name", "technology", "region", "country",
        "planning_authority", "planning_reference", "capacity_mw",
    ]
    present = pd.DataFrame(index=panel.index)
    for column in completeness_columns:
        values = panel[column] if column in panel.columns else pd.Series("", index=panel.index)
        present[column] = values.notna() & values.astype(str).str.strip().ne("")
    panel["data_completeness"] = present.mean(axis=1)
    panel["cfd_flag"] = (
        panel.get("cfd_round", pd.Series("", index=panel.index)).fillna("").astype(str).str.strip().ne("")
        | pd.to_numeric(panel.get("cfd_capacity_mw", np.nan), errors="coerce").fillna(0).gt(0)
    ).astype(int)
    for column in CATEGORICAL_FEATURES:
        panel[column] = panel[column].fillna("Unknown").astype(str)
    return panel


def _first_operational_dates(panel: pd.DataFrame) -> pd.Series:
    operational = panel[panel["stage"].eq("Operational")].groupby("project_key")["snapshot_date"].min()
    explicit = panel.groupby("project_key")["operational_date"].min()
    result = pd.concat([operational.rename("observed"), explicit.rename("explicit")], axis=1).min(axis=1)
    return result


def make_training_rows(panel: pd.DataFrame, horizon_years: int) -> pd.DataFrame:
    panel = add_features(panel)
    last_snapshot = panel["snapshot_date"].max()
    operational_dates = _first_operational_dates(panel)
    panel["first_operational_date"] = panel["project_key"].map(operational_dates)
    horizon_days = int(round(horizon_years * 365.25))
    panel["horizon_end"] = panel["snapshot_date"] + pd.to_timedelta(horizon_days, unit="D")

    before_operation = panel["first_operational_date"].isna() | (
        panel["snapshot_date"] < panel["first_operational_date"]
    )
    enough_follow_up = panel["horizon_end"] <= last_snapshot
    within_horizon = (
        panel["first_operational_date"].notna()
        & (panel["first_operational_date"] > panel["snapshot_date"])
        & (panel["first_operational_date"] <= panel["horizon_end"])
    )
    rows = panel[before_operation & (enough_follow_up | within_horizon)].copy()
    rows["target"] = within_horizon.loc[rows.index].astype(int)
    rows = rows[~rows["stage"].isin(["Stopped", "Decommissioned", "Operational"])]
    return rows


def build_pipeline() -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=5)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                LogisticRegression(
                    max_iter=2500,
                    class_weight="balanced",
                    C=0.7,
                    solver="liblinear",
                    random_state=42,
                ),
            ),
        ]
    )


def _time_split(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    unique_dates = sorted(rows["snapshot_date"].dropna().unique())
    if len(unique_dates) < 5:
        raise ValueError("At least five distinct labelled snapshots are required for time-based validation.")
    split_index = max(1, int(len(unique_dates) * 0.75))
    cutoff = pd.Timestamp(unique_dates[split_index])
    train = rows[rows["snapshot_date"] < cutoff].copy()
    test = rows[rows["snapshot_date"] >= cutoff].copy()
    if train["target"].nunique() < 2 or test["target"].nunique() < 2:
        cutoff = pd.Timestamp(unique_dates[max(1, int(len(unique_dates) * 0.65))])
        train = rows[rows["snapshot_date"] < cutoff].copy()
        test = rows[rows["snapshot_date"] >= cutoff].copy()
    return train, test, cutoff


def _safe_auc(y_true: pd.Series, probability: np.ndarray) -> float | None:
    if y_true.nunique() < 2:
        return None
    return float(roc_auc_score(y_true, probability))


def calibration_table(y_true: pd.Series, probability: np.ndarray) -> list[dict[str, Any]]:
    data = pd.DataFrame({"actual": y_true.to_numpy(), "probability": probability})
    bins = min(10, max(2, data["probability"].nunique()))
    try:
        data["bin"] = pd.qcut(data["probability"], q=bins, duplicates="drop")
    except ValueError:
        return []
    grouped = data.groupby("bin", observed=True).agg(
        mean_prediction=("probability", "mean"),
        observed_rate=("actual", "mean"),
        count=("actual", "size"),
    )
    return grouped.reset_index(drop=True).round(4).to_dict(orient="records")


def train_one(
    panel: pd.DataFrame,
    *,
    horizon_years: int,
    model_dir: Path,
) -> tuple[Pipeline, ModelResult, list[dict[str, Any]]]:
    rows = make_training_rows(panel, horizon_years)
    if len(rows) < 200 or rows["target"].nunique() < 2:
        raise RuntimeError(
            f"Not enough labelled data for {horizon_years}-year model: "
            f"{len(rows)} rows, classes={rows['target'].value_counts().to_dict()}"
        )
    train, test, cutoff = _time_split(rows)
    pipeline = build_pipeline()
    pipeline.fit(train[FEATURES], train["target"])
    probability = pipeline.predict_proba(test[FEATURES])[:, 1]
    prediction = (probability >= 0.5).astype(int)
    metrics = ModelResult(
        horizon_years=horizon_years,
        train_rows=len(train),
        test_rows=len(test),
        train_end=str(train["snapshot_date"].max().date()),
        test_start=str(test["snapshot_date"].min().date()),
        positive_rate_train=float(train["target"].mean()),
        positive_rate_test=float(test["target"].mean()),
        roc_auc=_safe_auc(test["target"], probability),
        brier_score=float(brier_score_loss(test["target"], probability)),
        accuracy=float(accuracy_score(test["target"], prediction)),
        precision=float(precision_score(test["target"], prediction, zero_division=0)),
        recall=float(recall_score(test["target"], prediction, zero_division=0)),
    )
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_dir / f"operation_{horizon_years}y.joblib")
    calibration = calibration_table(test["target"], probability)
    return pipeline, metrics, calibration


def predict_latest(panel: pd.DataFrame, models: dict[int, Pipeline]) -> pd.DataFrame:
    featured = add_features(panel)
    latest_date = featured["snapshot_date"].max()
    latest = featured[featured["snapshot_date"].eq(latest_date)].copy()
    latest = latest[~latest["stage"].isin(["Operational", "Stopped", "Decommissioned"])]
    for horizon, model in models.items():
        latest[f"prob_operational_{horizon}y"] = model.predict_proba(latest[FEATURES])[:, 1]
        latest[f"expected_capacity_{horizon}y_mw"] = (
            latest["capacity_mw"].fillna(0) * latest[f"prob_operational_{horizon}y"]
        )
    return latest


def train_all(
    panel_path: Path,
    model_dir: Path,
    forecast_path: Path,
    metrics_path: Path,
    horizons: tuple[int, ...] = (2, 3, 5),
) -> None:
    panel = load_panel(panel_path)
    models: dict[int, Pipeline] = {}
    report: dict[str, Any] = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "latest_snapshot": str(panel["snapshot_date"].max().date()),
        "models": {},
    }
    for horizon in horizons:
        print(f"Training {horizon}-year model...")
        model, metrics, calibration = train_one(
            panel,
            horizon_years=horizon,
            model_dir=model_dir,
        )
        models[horizon] = model
        report["models"][str(horizon)] = {
            **metrics.__dict__,
            "calibration": calibration,
        }
        auc_text = "N/A" if metrics.roc_auc is None else f"{metrics.roc_auc:.3f}"
        print(f"  ROC-AUC={auc_text}, Brier={metrics.brier_score:.3f}")

    latest = predict_latest(panel, models)
    forecast_path.parent.mkdir(parents=True, exist_ok=True)
    latest.to_csv(forecast_path, index=False, compression="gzip")
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {len(latest):,} current project forecasts to {forecast_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train time-based REPD project progression models.")
    parser.add_argument("--panel", type=Path, default=Path("data/processed/repd_panel.csv.gz"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument(
        "--forecasts",
        type=Path,
        default=Path("data/processed/latest_forecasts.csv.gz"),
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("data/processed/model_metrics.json"),
    )
    args = parser.parse_args()
    train_all(args.panel, args.model_dir, args.forecasts, args.metrics)


if __name__ == "__main__":
    main()
