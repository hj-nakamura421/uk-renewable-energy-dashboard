# UK Energy Infrastructure Intelligence Platform

[![CI](https://github.com/hj-nakamura421/uk-renewable-energy-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/hj-nakamura421/uk-renewable-energy-dashboard/actions/workflows/ci.yml)
[![Live app](https://img.shields.io/badge/Live_app-Open-FF4B4B?logo=streamlit&logoColor=white)](https://uk-renewable-project-screening.streamlit.app/)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)

A deployed Python and Streamlit product for exploring UK renewable-energy
infrastructure, reconstructing project histories and testing leakage-aware
time-to-operation forecasts.

**[Open the live product](https://uk-renewable-project-screening.streamlit.app/)**
· [Model card](MODEL_CARD.md)
· [Methodology](METHODOLOGY.md)
· [Architecture](ARCHITECTURE.md)

## Evidence at a glance

| Surface | Packaged evidence |
|---|---:|
| Historical project-snapshot rows | 103,579 |
| Linked project keys | 19,145 |
| Independent REPD snapshots | 15, spanning 2019–2026 |
| Survival-training intervals | 80,440 |
| Observed operation events | 928 |
| Automated test modules | 4 |
| Current release status | Research only |

The live Project Explorer currently exposes 13,009 planning records, regional
rankings, interactive maps, shortlisting, comparison, downloadable briefs and
an offshore feasibility model. The Forecasting surface adds two-, three- and
five-year probabilities, scenario testing, calibration evidence and a visible
Trust Centre.

## Why this project is different

This project does not promote a model simply because it is labelled “AI”.
Model v2 compares a transparent empirical survival model, a logistic survival
model and a CatBoost challenger on later historical project cohorts. The
CatBoost model is deployed only if it improves probability reliability.

Corrected temporal validation shows that the available 15 REPD snapshots are
not enough for decision-grade forecasts. That limitation is visible in the app
and model card instead of being hidden behind a high but misleading training
score.

## Product capabilities

- Search and filter current UK renewable-infrastructure projects
- Reconstruct project histories and development-stage changes
- Map projects with interactive zoom and probability colouring
- Rank regions using probability-weighted renewable capacity
- Estimate two-, three- and five-year time-to-operation probabilities
- Compare empirical, logistic and CatBoost survival candidates
- Inspect ROC-AUC, average precision, Brier score and calibration
- Stress-test Bank Rate, construction costs, grid delays, CfD support and policy
- Download filtered forecasts and individual project briefs
- Run automated source-grain, data-quality, leakage and scenario checks

## Modelling approach

The forecasting pipeline uses a discrete-time survival formulation. Each
project contributes annual at-risk intervals until it becomes operational or
its history is censored. This avoids labelling recently observed unresolved
projects as failures.

Features include:

- capacity, technology, region, country and stage;
- project age and time in its current stage;
- observed stage changes and capacity revisions;
- planning, consent and construction timing;
- CfD evidence and public-data completeness;
- developer and technology-region completion history available at the snapshot.

The test population contains only fully observed cohorts, and test projects are
purged from the corresponding survival-training rows. Promotion is driven by
temporal-holdout Brier score, not training accuracy or model complexity.

## External context

The packaged scenario context comes from:

- Office for National Statistics Consumer Prices Index;
- Office for National Statistics infrastructure Construction Output Price Index;
- Bank of England official Bank Rate database.

These values drive a clearly labelled stress-testing layer. They are not
treated as trained causal features while the dataset contains too few
independent time snapshots to estimate macroeconomic effects reliably.

## Architecture

```text
Official REPD snapshots ──► schema normalisation and entity linking
                                      │
                                      ├──► data-quality report
                                      ▼
                              project-snapshot panel
                                      │
                                      ▼
                         censored survival intervals
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
    Empirical baseline        Logistic survival        CatBoost challenger
             └────────────────────────┼────────────────────────┘
                                      ▼
                       temporal holdout + model policy
                                      │
          ONS + Bank of England ──────┼──► scenario stress layer
                                      ▼
                    Streamlit product + Trust Centre
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for module ownership and generated
artifacts.

## Quick start

```bash
git clone https://github.com/hj-nakamura421/uk-renewable-energy-dashboard.git
cd uk-renewable-energy-dashboard
uv sync --frozen --dev
uv run streamlit run app.py
```

Rebuild the models from the packaged historical panel:

```bash
uv run python bootstrap.py --skip-download
```

Run the verification suite:

```bash
uv run pytest -q
```

## Repository map

```text
uk-renewable-energy-dashboard/
├── app.py                         # Product shell and navigation
├── bootstrap.py                   # Reproducible data/model rebuild
├── pages/
│   ├── 1_Project_Explorer.py      # Screening and engineering exploration
│   └── 2_Forecasting.py           # Forecasting, scenarios and Trust Centre
├── src/
│   ├── data_quality.py            # Source-grain and integrity checks
│   ├── external_factors.py        # ONS and Bank of England context
│   ├── model.py                   # Survival features, validation and selection
│   ├── repd_clean.py              # Schema normalisation and entity linking
│   ├── repd_download.py           # Official-source ingestion
│   └── scenario.py                # Explicit stress assumptions
├── tests/                         # Data, leakage, model and scenario checks
├── data/processed/                # Versioned reproducibility artifacts
├── models/                        # Fitted research model bundles
├── MODEL_CARD.md
├── METHODOLOGY.md
└── ARCHITECTURE.md
```

## Reproducibility and safeguards

- Source snapshots are deduplicated at `snapshot_date × project_key`.
- Model features use only information visible at the origin snapshot.
- Partially followed projects are right-censored.
- Test projects are purged from matching survival-training rows.
- Model selection prioritises temporal-holdout Brier score.
- The app renders model status, data quality and limitations from artifacts.
- GitHub Actions compiles the code and runs the test suite on every change.

## Important limitations

- The panel contains only 15 independent source snapshots.
- REPD's inclusion threshold changed from 1 MW to 150 kW in 2021.
- Historical field definitions and coverage changed over time.
- Entity resolution can be imperfect when stable reference IDs are absent.
- Public data omit private finance, land, equipment, grid studies and contracts.
- Scenario adjustments are stress assumptions, not causal estimates.
- Outputs are research and portfolio work, not investment advice.

The [model card](MODEL_CARD.md) records the current status and promotion
criteria. [AI_USE.md](AI_USE.md) documents how AI-assisted work was reviewed.

## Author

HJ Nakamura — Mechanical Engineering, Imperial College London
