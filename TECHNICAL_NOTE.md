# Technical Note

## Tools Used

- Python
- Streamlit
- pandas
- Plotly
- pyproj
- Git/GitHub
- Streamlit Community Cloud

## App Architecture

```text
CSV dataset
→ pandas data loading
→ data cleaning
→ coordinate conversion
→ sidebar filters
→ project screening score
→ charts, tables and map
→ project brief generator
→ offshore wind model
→ deployed Streamlit app
```

## Main Components

### Data Loading

The app reads a local CSV file stored in the `data/` folder.

The file path is:

```text
data/renewable_projects.csv
```

The dataset is loaded using pandas.

### Data Cleaning

The app converts installed capacity into numeric values and removes rows where installed capacity is missing.

It also converts coordinate columns into numeric values before mapping.

### Coordinate Conversion

The dataset contains British National Grid coordinates.

The app uses `pyproj` to convert these coordinates from EPSG:27700 into latitude and longitude using EPSG:4326. This allows the projects to be plotted on an interactive map.

### Filtering

The sidebar filters allow the user to filter projects by:

- technology type
- development status
- region

All charts, tables, project reports and calculations update based on the selected filters.

### Visualisation

Plotly is used for:

- capacity by technology charts
- capacity by region charts
- capacity by development stage charts
- technology pipeline charts
- interactive project map
- sensitivity analysis chart

### Project Screening Score

The app calculates a simple score out of 100 for each project based on:

- project capacity
- development status
- technology type
- data completeness

This helps compare projects quickly within the dashboard.

### Offshore Wind Model

The offshore wind model estimates annual generation, turbine count, revenue, CAPEX, payback period and carbon savings using simplified engineering assumptions.

The assumptions can be changed using Streamlit sliders.

### Deployment

The app is deployed using Streamlit Community Cloud and version-controlled using Git/GitHub.

## Possible Improvements

Future improvements could include:

- automatically updating the dataset from the latest source
- generating PDF project briefs
- adding more detailed cost modelling
- adding planning-risk analysis
- integrating live carbon intensity data
- improving mobile layout
- adding user authentication for private datasets
