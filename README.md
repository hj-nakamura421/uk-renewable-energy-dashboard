# UK Energy Infrastructure Intelligence Platform

A Python and Streamlit platform for screening UK renewable energy infrastructure projects using public planning data, live grid context, geospatial mapping, regional opportunity ranking and simplified offshore wind feasibility modelling.

## Live App

https://uk-renewable-project-screening.streamlit.app/

## Project Summary

This project turns public UK renewable energy planning data into an interactive infrastructure screening tool. It allows users to search and filter renewable projects, compare regional capacity, map project locations, shortlist opportunities, generate project briefs and test simplified offshore wind feasibility assumptions.

The aim is to connect mechanical engineering, energy infrastructure and data analysis in a practical deployed project.

## What It Does

- Search and filter UK renewable energy projects
- Map project locations using converted British National Grid coordinates
- Rank regions by renewable infrastructure opportunity
- Identify high-scoring projects and under-construction projects
- Build and download a project shortlist
- Compare two renewable projects side by side
- Generate downloadable project briefs
- Add live GB grid context using carbon intensity and generation mix data
- Model simplified offshore wind generation, revenue, CAPEX, payback and carbon savings
- Explain project screening scores using capacity, planning maturity, technology relevance and data confidence
- Estimate project risk using development stage, scale, missing planning data and offshore complexity

### Overview

![Overview](assets/screenshots/overview.png)

### Map

![Map](assets/screenshots/map.png)

### Regional Ranking

![Regional Ranking](assets/screenshots/regional-ranking.png)

### Offshore Model

![Offshore Model](assets/screenshots/offshore-model.png)

## Tech Stack

- Python
- Streamlit
- pandas
- Plotly
- pyproj
- requests
- Git/GitHub
- Streamlit Community Cloud

## Data

The project uses public UK renewable energy planning data stored in:

```text
data/renewable_projects.csv
```

Live grid context is added using public carbon intensity and generation mix data.

## Engineering Relevance

This project demonstrates:

- data cleaning
- geospatial coordinate conversion
- renewable infrastructure project screening
- project risk scoring
- regional opportunity analysis
- basic techno-economic modelling
- offshore wind feasibility estimation
- dashboard deployment
- technical documentation and communication

## Project Structure

```text
offshore-energy-dashboard/
├── app.py
├── data/
│   └── renewable_projects.csv
├── assets/
│   └── screenshots/
│       ├── overview.png
│       ├── map.png
│       ├── regional-ranking.png
│       └── offshore-model.png
├── README.md
├── METHODOLOGY.md
├── TECHNICAL_NOTE.md
├── AI_USE.md
├── LEARNING_LOG.md
├── pyproject.toml
└── uv.lock
```

## Methodology

The platform includes a simplified screening model based on:

- capacity scale
- planning maturity
- technology relevance
- data confidence

It also includes a simplified risk level based on:

- development stage
- project scale
- missing planning information
- offshore infrastructure complexity

The offshore wind model estimates:

- annual energy generation
- turbine count
- annual revenue
- CAPEX
- simple payback period
- lifetime revenue
- annual carbon savings
- lifetime carbon savings

Full details are available in `METHODOLOGY.md`.

## Limitations

This is an educational and portfolio project. The screening score, risk level and offshore model are simplified and should not be treated as investment-grade analysis.

The model does not include detailed wind resource modelling, financing, operational expenditure, grid connection costs, curtailment, CfD pricing, construction risk, decommissioning costs or formal planning-risk modelling.

## Future Improvements

Potential future improvements include:

- automated dataset refresh
- PDF project reports
- more detailed offshore wind assumptions
- grid connection and constraint data
- richer regional energy infrastructure analysis
- user-defined scoring weightings
- AI-assisted project search and summarisation

## Author

HJ Nakamura  
Mechanical Engineering, Imperial College London