# Minimal setup

## 1. Copy this folder into your existing GitHub project

Keep a backup of the current `app.py` first.

## 2. Install dependencies

```bash
cd ~/Code/offshore-energy-dashboard
uv add streamlit pandas numpy plotly requests beautifulsoup4 lxml openpyxl xlrd scikit-learn joblib pyproj
```

## 3. Build the historical dataset and models

```bash
uv run python bootstrap.py
```

The script attempts to retrieve quarterly archived versions of the official GOV.UK REPD page through the Internet Archive, download the linked official government files, standardise them and train 2-, 3- and 5-year time-based models.

If archive retrieval is incomplete, manually download official historical REPD CSV/XLSX files and place them in:

```text
data/raw/repd/
```

Rename each file so it starts with its snapshot date, for example:

```text
2024-01-31_repd.csv
2024-04-30_repd.xlsx
```

Then run:

```bash
uv run python bootstrap.py --skip-download
```

## 4. Run the site

```bash
uv run streamlit run app.py
```

## 5. Deploy

Commit the processed files and models, but not the raw source files:

```bash
git add app.py bootstrap.py src requirements.txt METHODOLOGY.md README_SETUP.md data/processed models .streamlit

git commit -m "Add historical renewable project forecasting"
git push
```

For Render, use:

```text
Build command: pip install -r requirements.txt
Start command: streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

## What is automated and what is not

The code automates downloading where the archive exposes usable captures, cleaning, record linkage, label construction, chronological model training, validation metrics and the Streamlit interface. Historical government files can disappear from the live GOV.UK page, so a fully automatic archive download cannot be guaranteed. The application refuses to train on fewer than eight snapshots to prevent a convincing-looking but meaningless forecast.
