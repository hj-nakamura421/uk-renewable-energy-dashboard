# Methodology

## Purpose

This project is a renewable infrastructure screening tool built using Python and Streamlit. It demonstrates data cleaning, visualisation, geospatial mapping and simplified engineering-commercial analysis.

The aim is to show how a real-world public dataset can be turned into an interactive tool for exploring renewable energy project pipelines, comparing capacity by region and technology, and running basic offshore wind feasibility calculations.

## Dataset

The app uses UK renewable energy planning data stored locally as a CSV file.

The dataset contains project-level information including:

- site name
- operator or applicant
- technology type
- installed capacity
- development status
- region
- county
- planning authority
- planning application reference
- British National Grid coordinates

## Data Processing

The app performs the following processing steps:

1. Loads the CSV dataset using pandas.
2. Converts installed capacity into numeric values.
3. Removes rows without valid installed capacity.
4. Converts X and Y coordinates into numeric values.
5. Converts British National Grid coordinates into latitude and longitude using pyproj.
6. Applies user-selected filters for technology type, development status and region.
7. Calculates a simple project screening score for each filtered project.

## Project Screening Score

Each project receives a simplified score out of 100.

The score is based on:

- installed capacity
- development status
- technology type
- completeness of key project information

The screening score is not intended to be an investment ranking. It is a transparent early-stage indicator used to compare projects within the dashboard.

## Offshore Wind Feasibility Model

The offshore wind model estimates:

- annual energy generation
- number of turbines
- annual revenue
- total CAPEX
- simple payback period
- annual carbon savings
- lifetime carbon savings

## Formulae

Annual energy generation:

```text
Annual energy = capacity × capacity factor × 8760
```

Number of turbines:

```text
Number of turbines = project capacity ÷ turbine rating
```

Annual revenue:

```text
Annual revenue = annual energy generation × electricity price
```

Total CAPEX:

```text
Total CAPEX = project capacity × CAPEX per MW
```

Simple payback:

```text
Simple payback = total CAPEX ÷ annual revenue
```

Annual carbon savings:

```text
Annual carbon savings = annual energy generation × displaced grid carbon intensity
```

Lifetime carbon savings:

```text
Lifetime carbon savings = annual carbon savings × project lifetime
```

## Limitations

This is a simplified portfolio model. It does not include:

- detailed wind resource modelling
- turbine availability
- wake losses
- grid connection costs
- financing costs
- CfD pricing
- inflation
- operational expenditure
- decommissioning costs
- planning-risk modelling
- curtailment
- maintenance downtime

The tool should not be interpreted as an investment-grade renewable energy model.
