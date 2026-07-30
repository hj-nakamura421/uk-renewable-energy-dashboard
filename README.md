# UK Energy Infrastructure Intelligence Platform

A deployed Python and Streamlit platform for exploring UK renewable-energy
projects, reconstructing their histories and testing leakage-aware
time-to-operation forecasts.

**Live app:** https://uk-renewable-project-screening.streamlit.app/

## Why this project is different

The project does not promote a model simply because it is labelled “AI”.
Model v2 compares a transparent empirical survival model, a logistic survival
model and a CatBoost challenger on later historical project cohorts. The
CatBoost model is deployed only if it improves probability reliability.

The current packaged release is deliberately labelled **research-only**:
corrected validation shows that the available 15 REPD snapshots are not yet
enough for decision-grade forecasts. That limitation is visible in the app
rather than hidden behind a high but misleading accuracy number.

## Main capabilities

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
cd ~/Code/offshore-energy-dashboard
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
offshore-energy-dashboard/
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
