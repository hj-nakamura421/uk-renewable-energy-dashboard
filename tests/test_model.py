from __future__ import annotations

import numpy as np
import pandas as pd

from src.model import make_horizon_outcomes, make_survival_rows


def _featured_rows() -> pd.DataFrame:
    rows = [
        {
            "project_key": "negative",
            "snapshot_date": pd.Timestamp("2020-01-01"),
            "first_operational_date": pd.NaT,
            "stage": "Planning",
        },
        {
            "project_key": "positive",
            "snapshot_date": pd.Timestamp("2020-01-01"),
            "first_operational_date": pd.Timestamp("2021-06-01"),
            "stage": "Planning",
        },
        {
            "project_key": "recent-unresolved",
            "snapshot_date": pd.Timestamp("2024-09-01"),
            "first_operational_date": pd.NaT,
            "stage": "Planning",
        },
        {
            "project_key": "latest-marker",
            "snapshot_date": pd.Timestamp("2025-12-31"),
            "first_operational_date": pd.NaT,
            "stage": "Planning",
        },
    ]
    frame = pd.DataFrame(rows)
    for column in (
        "technology",
        "region",
        "country",
    ):
        frame[column] = "Example"
    for column in (
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
    ):
        frame[column] = 0.0
    return frame


def test_horizon_outcomes_exclude_unresolved_partial_cohorts() -> None:
    outcomes = make_horizon_outcomes(_featured_rows(), 2)
    assert set(outcomes["project_key"]) == {"negative", "positive"}
    assert outcomes.set_index("project_key").loc["negative", "target"] == 0
    assert outcomes.set_index("project_key").loc["positive", "target"] == 1


def test_survival_rows_handle_censoring_without_false_negatives() -> None:
    rows = make_survival_rows(_featured_rows(), max_horizon=3)
    positive = rows[rows["project_key"].eq("positive")]
    assert positive["forecast_interval"].tolist() == [1, 2]
    assert positive["target"].tolist() == [0, 1]
    recent = rows[rows["project_key"].eq("recent-unresolved")]
    assert recent["forecast_interval"].tolist() == [1]
    assert recent["target"].tolist() == [0]


def test_survival_target_is_binary() -> None:
    rows = make_survival_rows(_featured_rows(), max_horizon=3)
    assert set(np.unique(rows["target"])) <= {0, 1}
