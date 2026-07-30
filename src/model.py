from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HORIZONS = (2, 3, 5)
MAX_HORIZON = max(HORIZONS)
ACTIVE_STAGES = {"Inception", "Other", "Planning", "Consented", "Under Construction"}
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
    "months_in_current_stage",
    "stage_changes_count",
    "capacity_revision_count",
    "capacity_change_pct_from_first",
    "months_since_planning_submitted",
    "months_since_planning_granted",
    "months_since_construction_started",
    "observations_to_date",
    "developer_projects_prior",
    "developer_operations_prior",
    "developer_completion_rate_prior",
    "technology_region_projects_prior",
    "technology_region_operations_prior",
    "technology_region_completion_rate_prior",
    "forecast_interval",
]
CATEGORICAL_FEATURES = ["technology", "region", "country", "stage"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


class HazardModel(Protocol):
    name: str

    def fit(self, frame: pd.DataFrame, target: pd.Series) -> "HazardModel": ...

    def predict_hazard(self, frame: pd.DataFrame) -> np.ndarray: ...


@dataclass
class LogisticHazardModel:
    pipeline: Pipeline
    name: str = "survival_logistic"

    def fit(self, frame: pd.DataFrame, target: pd.Series) -> "LogisticHazardModel":
        self.pipeline.fit(frame[FEATURES], target)
        return self

    def predict_hazard(self, frame: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict_proba(frame[FEATURES])[:, 1]


@dataclass
class CatBoostHazardModel:
    model: CatBoostClassifier
    calibration_slope: float = 1.0
    calibration_intercept: float = 0.0
    name: str = "catboost_survival"

    @staticmethod
    def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
        prepared = frame[FEATURES].copy()
        for column in CATEGORICAL_FEATURES:
            prepared[column] = (
                prepared[column].fillna("Unknown").astype(str).replace("", "Unknown")
            )
        for column in NUMERIC_FEATURES:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        return prepared

    def fit(self, frame: pd.DataFrame, target: pd.Series) -> "CatBoostHazardModel":
        prepared = self._prepare(frame)
        self.model.fit(
            prepared,
            target.to_numpy(),
            cat_features=CATEGORICAL_FEATURES,
            verbose=False,
        )
        calibration_mask = frame.get(
            "interval_fully_observed",
            pd.Series(True, index=frame.index),
        ).astype(bool)
        calibration_frame = frame.loc[calibration_mask].copy()
        calibration_target = target.loc[calibration_mask]
        dates = sorted(calibration_frame["snapshot_date"].dropna().unique())
        if len(dates) >= 5:
            calibration_start = pd.Timestamp(dates[-2])
            score_mask = calibration_frame["snapshot_date"] >= calibration_start
            score_target = calibration_target.loc[score_mask]
            if (
                score_target.nunique() == 2
                and int(score_target.sum()) >= 10
            ):
                raw = self.model.predict_proba(
                    self._prepare(calibration_frame.loc[score_mask])
                )[:, 1]
                raw_logit = np.log(
                    np.clip(raw, 1e-5, 1 - 1e-5)
                    / np.clip(1 - raw, 1e-5, 1 - 1e-5)
                ).reshape(-1, 1)
                calibrator = LogisticRegression(C=0.25, max_iter=1000).fit(
                    raw_logit,
                    score_target.to_numpy(),
                )
                self.calibration_slope = float(calibrator.coef_[0, 0])
                self.calibration_intercept = float(calibrator.intercept_[0])
        return self

    def predict_hazard(self, frame: pd.DataFrame) -> np.ndarray:
        raw = self.model.predict_proba(self._prepare(frame))[:, 1]
        raw_logit = np.log(
            np.clip(raw, 1e-5, 1 - 1e-5)
            / np.clip(1 - raw, 1e-5, 1 - 1e-5)
        )
        calibrated_logit = (
            self.calibration_intercept + self.calibration_slope * raw_logit
        )
        return 1.0 / (1.0 + np.exp(-np.clip(calibrated_logit, -20, 20)))


@dataclass
class EmpiricalHazardModel:
    global_rates: dict[int, float] | None = None
    stage_rates: dict[tuple[int, str], float] | None = None
    detail_rates: dict[tuple[int, str, str], float] | None = None
    name: str = "empirical_survival"

    def fit(self, frame: pd.DataFrame, target: pd.Series) -> "EmpiricalHazardModel":
        data = frame[["forecast_interval", "stage", "technology"]].copy()
        data["target"] = target.to_numpy()
        data["stage"] = data["stage"].fillna("Unknown").astype(str)
        data["technology"] = data["technology"].fillna("Unknown").astype(str)

        global_summary = data.groupby("forecast_interval")["target"].agg(
            ["sum", "count"]
        )
        self.global_rates = {
            int(interval): float((row["sum"] + 1.0) / (row["count"] + 100.0))
            for interval, row in global_summary.iterrows()
        }

        stage_summary = data.groupby(["forecast_interval", "stage"])["target"].agg(
            ["sum", "count"]
        )
        self.stage_rates = {}
        for (interval, stage), row in stage_summary.iterrows():
            prior = self.global_rates[int(interval)]
            self.stage_rates[(int(interval), str(stage))] = float(
                (row["sum"] + 80.0 * prior) / (row["count"] + 80.0)
            )

        detail_summary = data.groupby(
            ["forecast_interval", "stage", "technology"]
        )["target"].agg(["sum", "count"])
        self.detail_rates = {}
        for (interval, stage, technology), row in detail_summary.iterrows():
            prior = self.stage_rates.get(
                (int(interval), str(stage)),
                self.global_rates[int(interval)],
            )
            self.detail_rates[
                (int(interval), str(stage), str(technology))
            ] = float((row["sum"] + 120.0 * prior) / (row["count"] + 120.0))
        return self

    def predict_hazard(self, frame: pd.DataFrame) -> np.ndarray:
        if (
            self.global_rates is None
            or self.stage_rates is None
            or self.detail_rates is None
        ):
            raise RuntimeError("Empirical hazard model has not been fitted.")
        values: list[float] = []
        for interval, stage, technology in zip(
            frame["forecast_interval"],
            frame["stage"].fillna("Unknown").astype(str),
            frame["technology"].fillna("Unknown").astype(str),
            strict=False,
        ):
            interval = int(interval)
            rate = self.detail_rates.get(
                (interval, stage, technology),
                self.stage_rates.get(
                    (interval, stage),
                    self.global_rates.get(interval, 0.01),
                ),
            )
            values.append(float(rate))
        return np.asarray(values)


def load_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path, compression="gzip", low_memory=False)
    for column in (
        "snapshot_date",
        "planning_submitted",
        "planning_granted",
        "under_construction_date",
        "operational_date",
    ):
        if column in panel:
            panel[column] = pd.to_datetime(panel[column], errors="coerce")
    return panel


def _first_operational_dates(panel: pd.DataFrame) -> pd.Series:
    observed = (
        panel[panel["stage"].eq("Operational")]
        .groupby("project_key")["snapshot_date"]
        .min()
    )
    explicit = panel.groupby("project_key")["operational_date"].min()
    return pd.concat(
        [observed.rename("observed"), explicit.rename("explicit")], axis=1
    ).min(axis=1)


def _month_difference(later: pd.Series, earlier: pd.Series) -> pd.Series:
    return (later - earlier).dt.days.div(30.4375).clip(lower=0)


def _add_track_record_features(panel: pd.DataFrame) -> pd.DataFrame:
    result = panel.copy()
    summary = (
        result.sort_values("snapshot_date")
        .groupby("project_key", as_index=False)
        .agg(
            first_seen=("snapshot_date", "min"),
            first_operational_date=("first_operational_date", "min"),
            operator=("operator", "first"),
            technology=("technology", "first"),
            region=("region", "first"),
        )
    )
    summary["operator"] = summary["operator"].fillna("Unknown").replace("", "Unknown")
    summary["technology"] = summary["technology"].fillna("Unknown").replace("", "Unknown")
    summary["region"] = summary["region"].fillna("Unknown").replace("", "Unknown")

    defaults = {
        "developer_projects_prior": 0.0,
        "developer_operations_prior": 0.0,
        "technology_region_projects_prior": 0.0,
        "technology_region_operations_prior": 0.0,
    }
    for column, value in defaults.items():
        result[column] = value

    for snapshot in sorted(result["snapshot_date"].dropna().unique()):
        snapshot = pd.Timestamp(snapshot)
        mask = result["snapshot_date"].eq(snapshot)
        prior_seen = summary[summary["first_seen"] < snapshot]
        prior_operational = summary[
            summary["first_operational_date"].notna()
            & (summary["first_operational_date"] < snapshot)
        ]

        developer_seen = prior_seen.groupby("operator")["project_key"].nunique()
        developer_operational = prior_operational.groupby("operator")[
            "project_key"
        ].nunique()
        tech_region_seen = prior_seen.groupby(["technology", "region"])[
            "project_key"
        ].nunique()
        tech_region_operational = prior_operational.groupby(["technology", "region"])[
            "project_key"
        ].nunique()

        operators = result.loc[mask, "operator"].fillna("Unknown").replace("", "Unknown")
        result.loc[mask, "developer_projects_prior"] = (
            operators.map(developer_seen).fillna(0).to_numpy()
        )
        result.loc[mask, "developer_operations_prior"] = (
            operators.map(developer_operational).fillna(0).to_numpy()
        )
        pairs = pd.MultiIndex.from_frame(
            result.loc[mask, ["technology", "region"]]
            .fillna("Unknown")
            .replace("", "Unknown")
        )
        result.loc[mask, "technology_region_projects_prior"] = (
            tech_region_seen.reindex(pairs).fillna(0).to_numpy()
        )
        result.loc[mask, "technology_region_operations_prior"] = (
            tech_region_operational.reindex(pairs).fillna(0).to_numpy()
        )

    result["developer_completion_rate_prior"] = (
        result["developer_operations_prior"] + 1.0
    ) / (result["developer_projects_prior"] + 10.0)
    result["technology_region_completion_rate_prior"] = (
        result["technology_region_operations_prior"] + 1.0
    ) / (result["technology_region_projects_prior"] + 10.0)
    return result


def add_features(panel: pd.DataFrame) -> pd.DataFrame:
    result = panel.copy()
    result["snapshot_date"] = pd.to_datetime(result["snapshot_date"], errors="coerce")
    result = result.sort_values(["project_key", "snapshot_date"]).reset_index(drop=True)
    result["capacity_mw"] = pd.to_numeric(result["capacity_mw"], errors="coerce")
    result["first_operational_date"] = result["project_key"].map(
        _first_operational_dates(result)
    )
    result["first_seen"] = result.groupby("project_key")["snapshot_date"].transform("min")
    result["project_age_years"] = _month_difference(
        result["snapshot_date"], result["first_seen"]
    ).div(12)
    result["log_capacity_mw"] = np.log1p(result["capacity_mw"].clip(lower=0))
    result["stage_rank"] = result["stage"].map(STAGE_RANK).fillna(1)

    result["planning_reference_present"] = (
        result["planning_reference"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .astype(int)
    )
    result["planning_granted_flag"] = (
        result["stage"].isin(["Consented", "Under Construction", "Operational"])
        | result["planning_granted"].notna()
    ).astype(int)
    result["under_construction_flag"] = (
        result["stage"].isin(["Under Construction", "Operational"])
        | result["under_construction_date"].notna()
    ).astype(int)
    completeness_columns = [
        "operator",
        "site_name",
        "technology",
        "region",
        "country",
        "planning_authority",
        "planning_reference",
        "capacity_mw",
    ]
    present = pd.DataFrame(index=result.index)
    for column in completeness_columns:
        values = (
            result[column]
            if column in result
            else pd.Series("", index=result.index, dtype=object)
        )
        present[column] = values.notna() & values.astype(str).str.strip().ne("")
    result["data_completeness"] = present.mean(axis=1)
    result["cfd_flag"] = (
        result.get("cfd_round", pd.Series("", index=result.index))
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        | pd.to_numeric(
            result.get("cfd_capacity_mw", pd.Series(np.nan, index=result.index)),
            errors="coerce",
        )
        .fillna(0)
        .gt(0)
    ).astype(int)

    grouped = result.groupby("project_key", sort=False)
    stage_changed = grouped["stage"].transform(
        lambda values: values.ne(values.shift()).astype(int)
    )
    result["stage_episode"] = stage_changed.groupby(result["project_key"]).cumsum()
    result["stage_changes_count"] = (result["stage_episode"] - 1).clip(lower=0)
    result["stage_start_date"] = result.groupby(
        ["project_key", "stage_episode"]
    )["snapshot_date"].transform("min")
    result["months_in_current_stage"] = _month_difference(
        result["snapshot_date"], result["stage_start_date"]
    )

    previous_capacity = grouped["capacity_mw"].shift()
    revision_threshold = np.maximum(previous_capacity.abs() * 0.01, 1.0)
    capacity_changed = (
        previous_capacity.notna()
        & result["capacity_mw"].notna()
        & result["capacity_mw"].sub(previous_capacity).abs().gt(revision_threshold)
    )
    result["capacity_revision_count"] = capacity_changed.groupby(
        result["project_key"]
    ).cumsum()
    first_capacity = grouped["capacity_mw"].transform("first")
    result["capacity_change_pct_from_first"] = (
        result["capacity_mw"].sub(first_capacity).div(first_capacity.replace(0, np.nan))
    ).clip(lower=-1, upper=5)

    for source, target in (
        ("planning_submitted", "months_since_planning_submitted"),
        ("planning_granted", "months_since_planning_granted"),
        ("under_construction_date", "months_since_construction_started"),
    ):
        result[source] = pd.to_datetime(result[source], errors="coerce")
        result[target] = _month_difference(result["snapshot_date"], result[source])
    result["observations_to_date"] = grouped.cumcount() + 1

    for column in CATEGORICAL_FEATURES:
        result[column] = result[column].fillna("Unknown").astype(str).replace("", "Unknown")
    result["operator"] = (
        result["operator"].fillna("Unknown").astype(str).replace("", "Unknown")
    )
    return _add_track_record_features(result)


def make_survival_rows(
    featured: pd.DataFrame,
    *,
    max_horizon: int = MAX_HORIZON,
    origin_before: pd.Timestamp | None = None,
    excluded_projects: set[str] | None = None,
) -> pd.DataFrame:
    last_snapshot = featured["snapshot_date"].max()
    active = featured[
        featured["stage"].isin(ACTIVE_STAGES)
        & (
            featured["first_operational_date"].isna()
            | (featured["first_operational_date"] > featured["snapshot_date"])
        )
    ].copy()
    if origin_before is not None:
        active = active[active["snapshot_date"] < origin_before]
    if excluded_projects:
        active = active[~active["project_key"].isin(excluded_projects)]

    follow_up_years = (
        last_snapshot - active["snapshot_date"]
    ).dt.days.div(365.25)
    time_to_event_years = (
        active["first_operational_date"] - active["snapshot_date"]
    ).dt.days.div(365.25)
    pieces: list[pd.DataFrame] = []
    for interval in range(1, max_horizon + 1):
        event_in_interval = (
            time_to_event_years.notna()
            & time_to_event_years.gt(interval - 1)
            & time_to_event_years.le(interval)
        )
        still_at_risk = time_to_event_years.isna() | time_to_event_years.gt(interval - 1)
        interval_observed = follow_up_years.ge(interval) | event_in_interval
        mask = still_at_risk & interval_observed
        if not mask.any():
            continue
        rows = active.loc[mask].copy()
        rows["forecast_interval"] = interval
        rows["target"] = event_in_interval.loc[mask].astype(int)
        rows["interval_fully_observed"] = follow_up_years.loc[mask].ge(interval)
        pieces.append(rows)
    if not pieces:
        return pd.DataFrame(columns=[*featured.columns, "forecast_interval", "target"])
    return pd.concat(pieces, ignore_index=True)


def make_horizon_outcomes(featured: pd.DataFrame, horizon: int) -> pd.DataFrame:
    last_snapshot = featured["snapshot_date"].max()
    active = featured[
        featured["stage"].isin(ACTIVE_STAGES)
        & (
            featured["first_operational_date"].isna()
            | (featured["first_operational_date"] > featured["snapshot_date"])
        )
    ].copy()
    active["horizon_end"] = active["snapshot_date"] + pd.to_timedelta(
        int(round(horizon * 365.25)), unit="D"
    )
    active = active[active["horizon_end"] <= last_snapshot].copy()
    active["target"] = (
        active["first_operational_date"].notna()
        & (active["first_operational_date"] <= active["horizon_end"])
    ).astype(int)
    return active


def build_logistic_model() -> LogisticHazardModel:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", min_frequency=10),
            ),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )
    pipeline = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "model",
                LogisticRegression(
                    max_iter=2500,
                    C=0.5,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )
    return LogisticHazardModel(pipeline=pipeline)


def build_empirical_model() -> EmpiricalHazardModel:
    return EmpiricalHazardModel()


def build_catboost_model(*, iterations: int = 350) -> CatBoostHazardModel:
    model = CatBoostClassifier(
        iterations=iterations,
        depth=6,
        learning_rate=0.04,
        loss_function="Logloss",
        eval_metric="Logloss",
        l2_leaf_reg=7.0,
        random_seed=42,
        allow_writing_files=False,
        thread_count=-1,
    )
    return CatBoostHazardModel(model=model)


def predict_cumulative_probability(
    model: HazardModel,
    origins: pd.DataFrame,
    horizon: int,
) -> np.ndarray:
    survival = np.ones(len(origins), dtype=float)
    for interval in range(1, horizon + 1):
        rows = origins.copy()
        rows["forecast_interval"] = interval
        hazard = np.clip(model.predict_hazard(rows), 0.0001, 0.9999)
        survival *= 1.0 - hazard
    return np.clip(1.0 - survival, 0.0, 1.0)


def _safe_auc(target: pd.Series, probability: np.ndarray) -> float | None:
    if target.nunique() < 2:
        return None
    return float(roc_auc_score(target, probability))


def _safe_average_precision(
    target: pd.Series, probability: np.ndarray
) -> float | None:
    if target.nunique() < 2:
        return None
    return float(average_precision_score(target, probability))


def calibration_table(
    target: pd.Series, probability: np.ndarray
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(
        {"actual": target.to_numpy(), "probability": np.asarray(probability)}
    )
    bins = min(8, max(2, int(frame["probability"].nunique())))
    try:
        frame["bin"] = pd.qcut(frame["probability"], q=bins, duplicates="drop")
    except ValueError:
        return []
    grouped = frame.groupby("bin", observed=True).agg(
        mean_prediction=("probability", "mean"),
        observed_rate=("actual", "mean"),
        count=("actual", "size"),
    )
    return grouped.reset_index(drop=True).round(5).to_dict(orient="records")


def _metrics(target: pd.Series, probability: np.ndarray) -> dict[str, Any]:
    prediction = np.asarray(probability) >= 0.5
    return {
        "roc_auc": _safe_auc(target, probability),
        "average_precision": _safe_average_precision(target, probability),
        "brier_score": float(brier_score_loss(target, probability)),
        "log_loss": float(log_loss(target, probability, labels=[0, 1])),
        "precision_at_50": float(
            precision_score(target, prediction, zero_division=0)
        ),
        "recall_at_50": float(recall_score(target, prediction, zero_division=0)),
        "mean_prediction": float(np.mean(probability)),
    }


def _split_outcomes(
    outcomes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    dates = sorted(outcomes["snapshot_date"].dropna().unique())
    if len(dates) < 3:
        raise RuntimeError("At least three fully observed origin cohorts are required.")
    test_count = 2 if len(dates) >= 6 else 1
    test_start = pd.Timestamp(dates[-test_count])
    train = outcomes[outcomes["snapshot_date"] < test_start].copy()
    test = outcomes[outcomes["snapshot_date"] >= test_start].copy()
    if train["target"].nunique() < 2 or test["target"].nunique() < 2:
        for candidate in reversed(dates[1:]):
            candidate = pd.Timestamp(candidate)
            train = outcomes[outcomes["snapshot_date"] < candidate].copy()
            test = outcomes[outcomes["snapshot_date"] >= candidate].copy()
            if train["target"].nunique() >= 2 and test["target"].nunique() >= 2:
                test_start = candidate
                break
    if train["target"].nunique() < 2 or test["target"].nunique() < 2:
        raise RuntimeError("Could not construct a temporal holdout containing both classes.")
    return train, test, test_start


def evaluate_candidates(featured: pd.DataFrame) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for horizon in HORIZONS:
        outcomes = make_horizon_outcomes(featured, horizon)
        horizon_report: dict[str, Any] = {
            "horizon_years": horizon,
            "fully_observed_rows": int(len(outcomes)),
            "fully_observed_snapshots": int(outcomes["snapshot_date"].nunique()),
            "candidates": {},
            "calibration": [],
        }
        try:
            train_origins, test_origins, test_start = _split_outcomes(outcomes)
            test_projects = set(test_origins["project_key"].astype(str))
            hazard_train = make_survival_rows(
                featured,
                origin_before=test_start,
                excluded_projects=test_projects,
            )
            if len(hazard_train) < 500 or hazard_train["target"].nunique() < 2:
                raise RuntimeError("Insufficient event rows after temporal/project purging.")

            models: list[HazardModel] = [
                build_empirical_model(),
                build_logistic_model(),
                build_catboost_model(iterations=260),
            ]
            probabilities: dict[str, np.ndarray] = {}
            for model in models:
                model.fit(hazard_train, hazard_train["target"])
                probability = predict_cumulative_probability(
                    model, test_origins, horizon
                )
                probabilities[model.name] = probability
                horizon_report["candidates"][model.name] = _metrics(
                    test_origins["target"], probability
                )

            base_rate = float(train_origins["target"].mean())
            base_probability = np.full(len(test_origins), base_rate)
            horizon_report["candidates"]["historical_base_rate"] = _metrics(
                test_origins["target"], base_probability
            )
            candidate_names = [
                "empirical_survival",
                "survival_logistic",
                "catboost_survival",
            ]
            selected = min(
                candidate_names,
                key=lambda name: horizon_report["candidates"][name]["brier_score"],
            )
            horizon_report.update(
                {
                    "train_origin_rows": int(len(train_origins)),
                    "train_hazard_rows": int(len(hazard_train)),
                    "test_rows": int(len(test_origins)),
                    "test_projects": int(test_origins["project_key"].nunique()),
                    "train_end": str(train_origins["snapshot_date"].max().date()),
                    "test_start": str(test_start.date()),
                    "test_end": str(test_origins["snapshot_date"].max().date()),
                    "positive_rate_train": float(train_origins["target"].mean()),
                    "positive_rate_test": float(test_origins["target"].mean()),
                    "selected_candidate": selected,
                    "calibration": calibration_table(
                        test_origins["target"], probabilities[selected]
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001
            horizon_report["validation_error"] = str(exc)
        report[str(horizon)] = horizon_report
    return report


def choose_final_model(validation: dict[str, Any]) -> tuple[str, str]:
    candidate_scores: dict[str, list[float]] = {
        "empirical_survival": [],
        "survival_logistic": [],
        "catboost_survival": [],
    }
    candidate_auc: dict[str, list[float]] = {
        "empirical_survival": [],
        "survival_logistic": [],
        "catboost_survival": [],
    }
    base_scores: list[float] = []
    for horizon in validation.values():
        candidates = horizon.get("candidates", {})
        for name in candidate_scores:
            values = candidates.get(name, {})
            if values.get("brier_score") is not None:
                candidate_scores[name].append(float(values["brier_score"]))
            if values.get("roc_auc") is not None:
                candidate_auc[name].append(float(values["roc_auc"]))
        base = candidates.get("historical_base_rate", {})
        if base.get("brier_score") is not None:
            base_scores.append(float(base["brier_score"]))

    if not any(candidate_scores.values()):
        return "empirical_survival", "research_only"
    mean_brier = {
        name: float(np.mean(scores)) if scores else math.inf
        for name, scores in candidate_scores.items()
    }
    mean_auc = {
        name: float(np.mean(candidate_auc[name])) if candidate_auc[name] else 0.5
        for name in candidate_scores
    }
    selected = min(mean_brier, key=mean_brier.get)
    selected_brier = mean_brier[selected]
    selected_auc = mean_auc[selected]
    base_brier = float(np.mean(base_scores)) if base_scores else math.inf
    if selected_auc >= 0.65 and selected_brier < base_brier * 0.98:
        status = "promising"
    elif selected_auc >= 0.58 and selected_brier <= base_brier * 1.05:
        status = "experimental"
    else:
        status = "research_only"
    return selected, status


def _positive_factors(row: pd.Series) -> str:
    factors: list[str] = []
    if row.get("stage") == "Under Construction":
        factors.append("Construction has started")
    elif row.get("stage") == "Consented":
        factors.append("Planning consent recorded")
    if row.get("cfd_flag", 0):
        factors.append("CfD support recorded")
    if row.get("developer_completion_rate_prior", 0) >= 0.25:
        factors.append("Above-average developer track record")
    if row.get("stage_changes_count", 0) >= 2:
        factors.append("Observed multi-stage progression")
    return " · ".join(factors[:3]) or "No strong positive signal in public data"


def _risk_factors(row: pd.Series) -> str:
    factors: list[str] = []
    if row.get("stage") in {"Inception", "Other", "Planning"}:
        factors.append("Early development stage")
    if row.get("months_in_current_stage", 0) >= 24:
        factors.append("Long time in current stage")
    if row.get("capacity_revision_count", 0) >= 2:
        factors.append("Repeated capacity revisions")
    if not row.get("planning_reference_present", 0):
        factors.append("Planning reference unavailable")
    if row.get("observations_to_date", 0) < 2:
        factors.append("Limited observed project history")
    return " · ".join(factors[:3]) or "No major public-data warning detected"


def predict_latest(
    featured: pd.DataFrame,
    models: dict[str, HazardModel],
    selected_model: str,
) -> pd.DataFrame:
    latest_date = featured["snapshot_date"].max()
    latest = featured[
        featured["snapshot_date"].eq(latest_date)
        & featured["stage"].isin(ACTIVE_STAGES)
    ].copy()
    model_column_prefix = {
        "empirical_survival": "baseline",
        "survival_logistic": "baseline",
        "catboost_survival": "ai",
    }
    for model_name, model in models.items():
        prefix = (
            "logistic"
            if model_name == "survival_logistic"
            else model_column_prefix[model_name]
        )
        for horizon in HORIZONS:
            latest[f"{prefix}_prob_operational_{horizon}y"] = (
                predict_cumulative_probability(model, latest, horizon)
            )
    selected_prefix = (
        "logistic" if selected_model == "survival_logistic" else model_column_prefix[selected_model]
    )
    for horizon in HORIZONS:
        probability_column = f"prob_operational_{horizon}y"
        latest[probability_column] = latest[
            f"{selected_prefix}_prob_operational_{horizon}y"
        ]
        latest[f"expected_capacity_{horizon}y_mw"] = (
            latest["capacity_mw"].fillna(0) * latest[probability_column]
        )
    latest["selected_model"] = selected_model
    latest["forecast_confidence"] = np.select(
        [
            latest["observations_to_date"].ge(4)
            & latest["data_completeness"].ge(0.75),
            latest["observations_to_date"].ge(2)
            & latest["data_completeness"].ge(0.55),
        ],
        ["Moderate", "Limited"],
        default="Low",
    )
    latest["positive_factors"] = latest.apply(_positive_factors, axis=1)
    latest["risk_factors"] = latest.apply(_risk_factors, axis=1)
    return latest


def train_all(
    panel_path: Path,
    model_dir: Path,
    forecast_path: Path,
    metrics_path: Path,
) -> dict[str, Any]:
    panel = load_panel(panel_path)
    featured = add_features(panel)
    validation = evaluate_candidates(featured)
    selected_model, release_status = choose_final_model(validation)
    hazard_rows = make_survival_rows(featured)
    if len(hazard_rows) < 500 or hazard_rows["target"].nunique() < 2:
        raise RuntimeError(
            "The project history did not produce enough survival training rows."
        )

    empirical = build_empirical_model().fit(hazard_rows, hazard_rows["target"])
    logistic = build_logistic_model().fit(hazard_rows, hazard_rows["target"])
    catboost = build_catboost_model().fit(hazard_rows, hazard_rows["target"])
    models: dict[str, HazardModel] = {
        empirical.name: empirical,
        logistic.name: logistic,
        catboost.name: catboost,
    }
    latest = predict_latest(featured, models, selected_model)

    model_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = model_dir / "forecasting_v2.joblib"
    bundle = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "selected_model": selected_model,
        "release_status": release_status,
        "features": FEATURES,
        "models": models,
    }
    joblib.dump(bundle, bundle_path)

    forecast_path.parent.mkdir(parents=True, exist_ok=True)
    latest.to_csv(forecast_path, index=False, compression="gzip")
    report = {
        "generated_at": bundle["generated_at"],
        "model_version": "2.0.0",
        "latest_snapshot": str(featured["snapshot_date"].max().date()),
        "panel_rows": int(len(featured)),
        "projects": int(featured["project_key"].nunique()),
        "snapshots": int(featured["snapshot_date"].nunique()),
        "survival_training_rows": int(len(hazard_rows)),
        "survival_events": int(hazard_rows["target"].sum()),
        "selected_model": selected_model,
        "release_status": release_status,
        "models": validation,
        "methodology_notes": [
            "The target is discrete annual time-to-operation hazard with right censoring.",
            "All validation targets come only from fully observed origin cohorts.",
            "Test projects are purged from the survival training rows for each holdout.",
            "CatBoost is selected only when its temporal-holdout Brier score improves.",
            "External macro variables are scenario inputs, not trained model features, "
            "because the panel contains too few independent time snapshots.",
        ],
        "known_limitations": [
            "Only a small number of independent REPD snapshots are available.",
            "The REPD inclusion threshold changed in 2021.",
            "Entity resolution can be imperfect when stable reference IDs are absent.",
            "Public sources do not reveal private finance, land, equipment or contract terms.",
            "Forecasts are research estimates, not investment advice.",
        ],
    }
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train leakage-aware discrete-time survival forecasting models."
    )
    parser.add_argument(
        "--panel",
        type=Path,
        default=Path("data/processed/repd_panel.csv.gz"),
    )
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
    report = train_all(args.panel, args.model_dir, args.forecasts, args.metrics)
    print(
        f"Saved Model v2 ({report['selected_model']}, {report['release_status']}) "
        f"with {report['survival_training_rows']:,} survival rows."
    )


if __name__ == "__main__":
    main()
