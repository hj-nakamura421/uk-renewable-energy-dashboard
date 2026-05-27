# UK Renewable Energy Dashboard

A Python and Streamlit dashboard for exploring UK renewable energy infrastructure projects, with a simplified offshore wind feasibility calculator.

## Project Aim

The aim of this project is to combine data analysis, engineering assumptions and simple commercial modelling to assess UK renewable energy projects, especially offshore wind.

## Features

- Explore UK renewable energy projects
- Filter by technology type, development status and region
- View total and average installed capacity
- Visualise installed capacity by technology
- Visualise installed capacity by region
- Identify the top 10 largest projects
- Plot projects on a UK map
- Export filtered project data as CSV
- Estimate offshore wind annual energy generation
- Estimate number of turbines
- Estimate annual revenue
- Estimate CAPEX
- Estimate simple payback period
- Estimate annual and lifetime carbon savings

## Tools Used

- Python
- Streamlit
- pandas
- Plotly
- pyproj
- Git/GitHub

## Engineering Calculations

The offshore wind calculator uses simplified formulas for:

- annual energy generation
- turbine count
- annual revenue
- CAPEX
- simple payback
- carbon savings

Full details are in `METHODOLOGY.md`.

## How to Run Locally

```bash
uv run streamlit run app.py