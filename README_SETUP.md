# Setup and rebuild guide

## Run the packaged application

```bash
git clone https://github.com/hj-nakamura421/uk-renewable-energy-dashboard.git
cd uk-renewable-energy-dashboard
uv sync
uv run streamlit run app.py
```

On macOS, `run_app.command` performs these steps when double-clicked.

## Rebuild using the packaged historical panel

```bash
uv run python bootstrap.py --skip-download
```

This command:

1. reuses `data/processed/repd_panel.csv.gz` when raw files are absent;
2. regenerates the data-quality report;
3. refreshes official ONS and Bank of England context;
4. trains the empirical, logistic and CatBoost survival candidates;
5. runs leakage-safe temporal holdouts;
6. selects the most reliable candidate;
7. writes the current forecast and model artifacts.

Use `--skip-external` to keep the packaged external-context file.

## Rebuild from source REPD files

Place official CSV/XLSX files in `data/raw/repd/`. Each filename should begin
with the source date:

```text
2024-01-31_repd.csv
2024-04-30_repd.xlsx
```

Then run:

```bash
uv run python bootstrap.py --skip-download
```

To attempt archive discovery automatically:

```bash
uv run python bootstrap.py --frequency monthly
```

Archive availability is not guaranteed, so the packaged processed panel is kept
for reproducibility.

## Test

```bash
uv run pytest -q
```

## Deploy

Streamlit Community Cloud:

```text
Entry point: app.py
Python: 3.13
```

Render:

```text
Build command: pip install -r requirements.txt
Start command: streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

The processed data and fitted Model v2 bundle must be committed for hosts that
do not rebuild external data during deployment.
