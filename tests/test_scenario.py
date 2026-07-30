from __future__ import annotations

import pandas as pd

from src.scenario import Scenario, apply_scenario


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "prob_operational_3y": [0.20, 0.60],
            "stage": ["Planning", "Under Construction"],
            "technology": ["Offshore Wind", "Solar Photovoltaics"],
            "cfd_flag": [0, 1],
        }
    )


def test_neutral_scenario_is_identity() -> None:
    frame = _frame()
    stressed = apply_scenario(frame, "prob_operational_3y", Scenario())
    pd.testing.assert_series_equal(
        stressed,
        frame["prob_operational_3y"].rename(
            "scenario_prob_operational_3y"
        ),
        check_exact=False,
        rtol=1e-10,
    )


def test_adverse_scenario_reduces_probability() -> None:
    frame = _frame()
    stressed = apply_scenario(
        frame,
        "prob_operational_3y",
        Scenario(
            bank_rate_change_pp=2.0,
            construction_cost_change_pct=15.0,
            policy_regime="Restrictive",
            grid_delay_years=2.0,
        ),
    )
    assert stressed.lt(frame["prob_operational_3y"]).all()


def test_supportive_scenario_increases_probability() -> None:
    frame = _frame()
    stressed = apply_scenario(
        frame,
        "prob_operational_3y",
        Scenario(policy_regime="Supportive", new_cfd_support=True),
    )
    assert stressed.gt(frame["prob_operational_3y"]).all()
