# Technical Note

## Stack

- Python 3.13
- Streamlit
- pandas and NumPy
- Plotly
- scikit-learn
- CatBoost
- pyproj
- requests, Beautiful Soup and lxml
- pytest and GitHub Actions

## Data path

```text
official files
→ schema normalisation
→ project entity linking
→ project-snapshot panel
→ data-quality checks
→ leakage-safe feature engineering
→ discrete-time survival intervals
→ temporal model comparison
→ current forecasts
→ Streamlit Trust Centre and Scenario Lab
```

## Why survival modelling

Many projects are unresolved when the historical panel ends. A binary
classifier cannot safely call those projects failures at horizons that have not
elapsed. Discrete-time survival rows represent only complete at-risk intervals
and observed operations.

## Why CatBoost is a challenger

CatBoost can model nonlinear categorical interactions, but the data decides
whether it is used. The packaged release does not promote it because later
cohort reliability is not consistently better than the transparent baseline.

## Why macro effects are separate

There are thousands of project rows but only 15 independent source dates.
Duplicating one Bank Rate or inflation observation across thousands of rows does
not create thousands of macro observations. External effects therefore power a
transparent scenario tool rather than a falsely precise trained coefficient.

## Quality controls

- unique snapshot-project grain;
- allowed project-stage domain;
- non-negative capacity;
- no future snapshot dates;
- visible fallback entity-key rate;
- fully observed evaluation cohorts;
- test-project purging;
- rare-event metrics;
- automated label and scenario tests.
