from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Scenario:
    bank_rate_change_pp: float = 0.0
    construction_cost_change_pct: float = 0.0
    policy_regime: str = "Neutral"
    grid_delay_years: float = 0.0
    new_cfd_support: bool = False


POLICY_LOG_ODDS = {
    "Restrictive": -0.40,
    "Neutral": 0.0,
    "Supportive": 0.35,
}


def _logit(probability: np.ndarray) -> np.ndarray:
    clipped = np.clip(probability.astype(float), 0.005, 0.995)
    return np.log(clipped / (1.0 - clipped))


def _expit(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -20, 20)))


def apply_scenario(
    frame: pd.DataFrame,
    probability_column: str,
    scenario: Scenario,
) -> pd.Series:
    """Apply an explicit, bounded stress-test adjustment to model probabilities.

    These adjustments are deliberately not represented as learned causal effects.
    They let users explore consistent directional assumptions while the historical
    macro sample remains too small for defensible coefficient estimation.
    """

    probability = pd.to_numeric(frame[probability_column], errors="coerce").fillna(0.0)
    stage = frame.get("stage", pd.Series("Other", index=frame.index)).fillna("Other")
    technology = frame.get(
        "technology", pd.Series("Unknown", index=frame.index)
    ).fillna("Unknown")
    cfd_flag = pd.to_numeric(
        frame.get("cfd_flag", pd.Series(0, index=frame.index)), errors="coerce"
    ).fillna(0)

    early_stage_multiplier = stage.map(
        {
            "Inception": 1.35,
            "Other": 1.20,
            "Planning": 1.15,
            "Consented": 0.90,
            "Under Construction": 0.45,
        }
    ).fillna(1.0)
    capital_intensity = technology.astype(str).str.lower().map(
        lambda value: (
            1.35
            if "offshore" in value
            else 1.15
            if any(word in value for word in ("wind", "tidal", "hydro", "biomass"))
            else 0.90
            if "solar" in value
            else 1.0
        )
    )

    adjustment = (
        -0.11
        * float(scenario.bank_rate_change_pp)
        * early_stage_multiplier
        * capital_intensity
    )
    adjustment += (
        -0.018
        * float(scenario.construction_cost_change_pct)
        * early_stage_multiplier
        * capital_intensity
    )
    adjustment += POLICY_LOG_ODDS.get(scenario.policy_regime, 0.0)
    adjustment += -0.42 * float(scenario.grid_delay_years) * early_stage_multiplier
    if scenario.new_cfd_support:
        adjustment += np.where(cfd_flag.gt(0), 0.0, 0.45)

    stressed = _expit(_logit(probability.to_numpy()) + np.asarray(adjustment))
    return pd.Series(stressed, index=frame.index, name=f"scenario_{probability_column}")


def scenario_summary(scenario: Scenario) -> list[str]:
    messages: list[str] = []
    if scenario.bank_rate_change_pp:
        messages.append(f"Bank Rate change: {scenario.bank_rate_change_pp:+.1f} pp")
    if scenario.construction_cost_change_pct:
        messages.append(
            f"Construction-cost shock: {scenario.construction_cost_change_pct:+.0f}%"
        )
    if scenario.policy_regime != "Neutral":
        messages.append(f"Policy regime: {scenario.policy_regime.lower()}")
    if scenario.grid_delay_years:
        messages.append(f"Grid delay: {scenario.grid_delay_years:.1f} years")
    if scenario.new_cfd_support:
        messages.append("Assume new CfD support")
    return messages or ["Current-conditions reference scenario"]
