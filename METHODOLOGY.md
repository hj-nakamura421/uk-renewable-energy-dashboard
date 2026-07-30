# Forecasting Methodology

## Objective

The baseline models estimate whether a non-operational REPD project will first appear as operational within two, three or five years of a historical snapshot.

## Historical panel

Official REPD extracts are converted into a project–snapshot panel. Records are linked principally through `Ref ID`, `Old Ref ID` and revised-application reference fields. A fallback project key is used where no identifier exists.

## Labels and censoring

A row is positive when the project becomes operational after the snapshot and within the selected horizon. A negative row is used only when the historical dataset extends beyond the end of that horizon and the project has not become operational. Rows without sufficient follow-up are excluded rather than incorrectly labelled as failures.

## Features

- logarithm of installed capacity
- project age at the snapshot
- development-stage rank
- planning reference present
- planning permission / consent indicator
- construction indicator
- data-completeness score
- CfD indicator where available
- technology, region, country and stage

## Validation

The split is chronological: earlier snapshots train the model and later snapshots test it. Reported metrics include ROC-AUC, Brier score, precision, recall and a calibration table.

## Aggregate forecasts

For a group of projects, expected future capacity is calculated as the sum of each project's capacity multiplied by its estimated probability of becoming operational within the chosen horizon.

## Known limitations

- The REPD threshold changed from 1 MW to 150 kW in 2021.
- Status definitions and field names have changed over time.
- Revised applications and project renaming can create matching errors.
- Public data do not capture all financing, grid, land, consenting or supply-chain risks.
- Outputs are not investment advice or an investment-grade valuation.
