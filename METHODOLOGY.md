# Methodology

## Dataset

This dashboard uses the UK Renewable Energy Planning Database. The dataset includes renewable electricity projects with information such as site name, technology type, installed capacity, development status, region and coordinates.

## Dashboard Calculations

### Total capacity

Total capacity is calculated by summing the `Installed Capacity (MWelec)` column after applying the selected filters.

### Average capacity

Average project capacity is calculated as:

```text
Average capacity = total filtered capacity / number of filtered projects
