# Architecture

```text
Official historical REPD files
        │
        ▼
Download and source manifest ── src/repd_download.py
        │
        ▼
Schema normalisation, entity linking, coordinates ── src/repd_clean.py
        │
        ├──────────────► Data-quality report ── src/data_quality.py
        │
        ▼
Project-snapshot panel
        │
        ▼
Leakage-safe temporal features and censored intervals ── src/model.py
        │
        ├─ Empirical survival baseline
        ├─ Logistic survival model
        └─ CatBoost AI challenger
        │
        ▼
Temporal holdouts, model selection and forecast artifacts
        │
        ├──────────────► Trust Centre
        │
        ▼
Streamlit forecasting dashboard

ONS CPI ────────────────┐
ONS Construction OPI ──┼─► Official macro context ─► Scenario Lab
Bank of England rate ───┘
```

## Generated artifacts

| Artifact | Purpose |
|---|---|
| `repd_panel.csv.gz` | Linked project-snapshot panel |
| `latest_forecasts.csv.gz` | Current project forecasts and evidence fields |
| `model_metrics.json` | Holdout results, selection and model status |
| `data_quality_report.json` | Grain, coverage and integrity checks |
| `external_context.csv` | Monthly official economic context |
| `external_metadata.json` | Source URLs, timestamps and caveats |
| `forecasting_v2.joblib` | Reproducible fitted model bundle |

## Application surfaces

- `app.py` controls hidden Streamlit multipage navigation and shared styling.
- `pages/1_Project_Explorer.py` provides infrastructure screening and engineering
  exploration.
- `pages/2_Forecasting.py` provides the simplified six-tab forecasting workflow.
- `shared_ui.py` provides the common portfolio footer.
