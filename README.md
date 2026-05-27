# UK Renewable Project Screening Dashboard

An interactive UK renewable energy dashboard built with Python and Streamlit for exploring renewable energy planning data, screening infrastructure projects, mapping project locations and modelling offshore wind feasibility.

## Live App

https://uk-renewable-project-screening.streamlit.app/

## Project Summary

This project turns public UK renewable energy planning data into an interactive project-screening dashboard. It allows users to search and filter projects, compare regional capacity, map renewable developments, generate project briefs and run simplified offshore wind feasibility calculations.

## Keywords

UK renewable energy dashboard, renewable project screening, renewable energy planning database, offshore wind feasibility model, renewable infrastructure dashboard.

## Live App

(https://uk-renewable-energy-dashboard.streamlit.app/)

## Project Summary

This project turns public renewable energy planning data into an interactive project-screening tool.

It allows users to explore renewable project pipelines, compare regional capacity, map developments, generate project briefs and run simplified offshore wind feasibility calculations.

## Why I Built This

I built this project to connect mechanical engineering, energy infrastructure and data analysis.

The aim was to demonstrate that I can take a real-world dataset, clean it, analyse it, build a useful interactive tool, deploy it online and explain the engineering assumptions behind it.

## Features

- Filter renewable projects by technology, region and development status
- View total, average and project-level capacity
- Analyse capacity by technology and region
- Analyse capacity by development stage
- Map UK renewable energy projects
- Generate project briefs
- Compare similar projects
- Score projects using a transparent screening model
- Estimate offshore wind generation, revenue, CAPEX and payback
- Estimate annual and lifetime carbon savings
- Run sensitivity analysis on capacity factor
- Download filtered project data

## Tools Used

- Python
- Streamlit
- pandas
- Plotly
- pyproj
- Git/GitHub
- Streamlit Community Cloud

## Engineering Relevance

This project demonstrates:

- data cleaning
- geospatial data handling
- engineering assumptions
- infrastructure project screening
- basic techno-economic modelling
- dashboard deployment
- documentation and communication

## Project Structure

```text
offshore-energy-dashboard/
├── app.py
├── data/
│   └── renewable_projects.csv
├── README.md
├── METHODOLOGY.md
├── TECHNICAL_NOTE.md
├── AI_USE.md
├── LEARNING_LOG.md
├── pyproject.toml
└── uv.lock
```

## Methodology

The offshore wind model estimates:

- annual energy generation
- turbine count
- annual revenue
- CAPEX
- simple payback period
- carbon savings

Full details are available in `METHODOLOGY.md`.

## Limitations

This is a simplified portfolio project. It is not an investment-grade renewable energy model and does not include detailed wind resource modelling, financing, operational expenditure, grid connection cost, curtailment or planning-risk modelling.

## Author

H N  
Mechanical Engineering student, Imperial College London
