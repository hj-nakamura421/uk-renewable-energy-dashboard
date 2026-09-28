# UK Renewable Infrastructure Intelligence — Modelling Workspace

An independent decision-support project built around UK renewable planning
histories. I reconstructed those histories, developed time-to-operation models
and tested them on later project cohorts. When validation showed useful relative
ranking but unreliable literal probabilities, I redesigned the public ranking
interface around the evidence the model could support.

**Evidence boundary: only 15 independent REPD snapshots.** Probability calibration
did not clear the public release criterion. The [public Forecast v2.2 platform](https://uk-renewable-intelligence.github.io/)
publishes a two-year relative ranking and withholds project-level percentages
from that interface. Its experimental capacity aggregates retain uncalibrated
research scores; aggregation does not repair probability error.

This repository is the **Python/Streamlit research workspace**. Its Model v2
pipeline and probability outputs remain available for reproducibility and
experimentation. Its Python package version is **0.2.0**; the separate web
platform is **2.2.0**, serving forecasting release **v2.2**. These identify
different components.

## For portfolio reviewers — 2-minute tour

1. [Open the public dashboard](https://uk-renewable-intelligence.github.io/).
2. [Review forecasting evidence](https://uk-renewable-intelligence.github.io/forecasting/#model-evidence).
3. [See why literal probabilities were withheld](https://uk-renewable-intelligence.github.io/forecasting/#forecast-performance).
4. [Read the engineering case study](https://uk-renewable-intelligence.github.io/about/), then inspect [methodology](METHODOLOGY.md) and [model source](src/model.py).

[Live research workspace](https://uk-renewable-project-screening.streamlit.app/) ·
[Public interface and v2.2 audit source](https://github.com/uk-renewable-intelligence/uk-renewable-intelligence.github.io)

## What I engineered

- Reconciled changing REPD snapshots and reconstructed project histories in [the cleaning pipeline](src/repd_clean.py).
- Built censored time-to-event forecasting and compared empirical, logistic and CatBoost candidates in [the model pipeline](src/model.py).
- Designed temporal holdouts, removed test projects from training histories and evaluated ranking and calibration separately.
- Added [data-quality checks](src/data_quality.py), [external-context ingestion](src/external_factors.py), [scenario analysis](src/scenario.py) and [automated tests](tests/).
- Extended the project with horizon release gates and a CatBoost tie-breaker in the [public platform's audit](https://github.com/uk-renewable-intelligence/uk-renewable-intelligence.github.io/tree/main/analysis).
- Built the JavaScript/Leaflet public interface and automated static deployment in the [web repository](https://github.com/uk-renewable-intelligence/uk-renewable-intelligence.github.io).

## What failed / what I changed

Earlier fixed-horizon evaluation included projects without sufficient follow-up,
giving misleading test outcomes. I rebuilt the targets with censoring and used
fully observed, project-purged temporal cohorts.

The later calibration audit found that useful ranking did not justify literal
probabilities. I withheld project percentages from the public ranking interface
and the five-year public output. The standalone CatBoost challenger also failed
to improve on the empirical ordering; v2.2 uses it only to resolve ties where
the evaluated combination improved ranking. The [audit and release decisions](https://uk-renewable-intelligence.github.io/forecasting/#forecast-performance)
remain public.

## Development timeline

- **Initial prototype / v1:** fixed-horizon prediction and project exploration; later review exposed incomplete-follow-up bias.
- **Model v2:** censored survival targets, temporal holdouts and empirical/logistic/CatBoost comparison in this workspace.
- **Public ranking release:** calibration audit and withdrawal of literal project probabilities from the ranking interface.
- **Forecast v2.2:** empirical ordering with a CatBoost tie-breaker, published validation evidence and an interactive public workbench.

## Research workspace capabilities

- Search and filter current UK renewable-infrastructure projects
- Explore project histories and development-stage changes
- Map projects with interactive zoom and probability colouring
- Estimate two-, three- and five-year time-to-operation probabilities
- Compare the deployed model with logistic and CatBoost challengers
- Inspect ROC-AUC, average precision, Brier score and calibration
- View positive signals, public-data risks and confidence levels
- Stress-test Bank Rate, construction costs, grid delays, CfD support and
  policy conditions
- Download filtered forecasts and individual project briefs
- Explore regional probability-weighted capacity
- Run automated data-quality checks and GitHub Actions tests

## Model v2

Survival modelling estimates how the chance of reaching operation changes as a
project spends longer in development. Censoring means an unresolved project
contributes only its observed follow-up, without being counted as a failure
because the data collection ended.

The forecasting pipeline uses a discrete-time survival formulation. Each
project contributes annual at-risk intervals until it becomes operational or
its history is censored. This prevents recently observed unresolved projects
from being incorrectly labelled as failures.

Features include:

- capacity, technology, region, country and stage
- project age and time in current stage
- observed stage changes and capacity revisions
- planning, consent and construction timing
- CfD evidence and public-data completeness
- developer completion history available at the snapshot
- technology-region completion history available at the snapshot

The test population contains only fully observed cohorts. Test projects are
purged from the corresponding survival-training rows.

## External context

The packaged macro context is downloaded from:

- Office for National Statistics Consumer Prices Index
- Office for National Statistics infrastructure Construction Output Price Index
- Bank of England official Bank Rate database

These values power a clearly labelled scenario layer. They are not treated as
trained causal features while the dataset contains too few independent time
snapshots to estimate political or inflation effects reliably.

## Quick start

### Simplest option on macOS

Double-click `run_app.command`.

### Terminal

```bash
git clone https://github.com/hj-nakamura421/uk-renewable-energy-dashboard.git
cd uk-renewable-energy-dashboard
uv sync
uv run streamlit run app.py
```

To refresh official macro context and rebuild the models from the packaged
historical panel:

```bash
uv run python bootstrap.py --skip-download
```

To run the checks:

```bash
uv run pytest -q
```

## Project structure

```text
uk-renewable-energy-dashboard/
├── app.py
├── bootstrap.py
├── shared_ui.py
├── pages/
│   ├── 1_Project_Explorer.py
│   └── 2_Forecasting.py
├── src/
│   ├── data_quality.py
│   ├── external_factors.py
│   ├── model.py
│   ├── repd_clean.py
│   ├── repd_download.py
│   └── scenario.py
├── tests/
├── data/
│   ├── processed/
│   └── raw/repd/
├── models/
├── MODEL_CARD.md
├── METHODOLOGY.md
├── ARCHITECTURE.md
└── PRODUCT_ROADMAP.md
```

## Reproducibility and safeguards

- Source snapshots are deduplicated at `snapshot_date × project_key`.
- Model features are derived only from information visible at the origin
  snapshot.
- Partially followed projects are right-censored.
- Model promotion is based primarily on temporal-holdout Brier score, not
  training accuracy.
- The app exposes model status, data quality and limitations.
- Tests protect label construction, censoring, scenario direction and source
  grain.

## Important limitations

- The panel contains only 15 independent source snapshots.
- REPD's inclusion threshold changed from 1 MW to 150 kW in 2021.
- Historical field definitions and coverage changed over time.
- Entity resolution can be imperfect when stable reference IDs are absent.
- Public data omit private finance, land, equipment, detailed grid studies and
  confidential contract terms.
- Scenario adjustments are stress assumptions, not causal estimates.
- Outputs are research and portfolio work, not investment advice.

## Author

HJ Nakamura  
Mechanical Engineering, Imperial College London
