# Forecasting Methodology

## Objective

Estimate the probability that a non-operational UK renewable-infrastructure
project first becomes operational within two, three or five years of a public
REPD snapshot.

## Historical panel and grain

Official REPD extracts are standardised into one record per:

```text
snapshot_date × project_key
```

Reference IDs, old IDs and revised-application fields are used to link projects
through time. Records without a usable reference receive a documented fallback
key based on project name, planning authority and capacity.

## Leakage repair

The previous fixed-horizon classifier included later positive projects even
when the corresponding cohort did not yet have enough follow-up for failures to
be observed. Later test sets therefore contained only positive outcomes.

Model v2 separates training and evaluation:

- training uses annual survival intervals and right censoring;
- evaluation uses only origin cohorts whose complete horizon is observable;
- test projects are removed from the corresponding survival-training rows;
- the model never receives project identifiers as features;
- track-record features count only events dated before the origin snapshot.

## Discrete-time survival target

For every active project snapshot, annual intervals are created while the
project remains at risk. An interval is:

- positive when operation is first observed during that interval;
- negative when the project is observed to remain non-operational throughout
  the complete interval;
- omitted after operation;
- omitted when an unresolved interval is only partially observed.

Annual hazards are converted to cumulative probability:

```text
P(operation by year h) = 1 - product(1 - annual hazard_t), t = 1…h
```

## Features

### Project state

- logarithm of capacity
- project age
- stage and stage rank
- planning-reference availability
- consent and construction indicators
- CfD evidence
- public-data completeness

### Movement and delay

- months in current stage
- observed number of stage changes
- observed capacity-revision count
- capacity change relative to first observation
- months since planning submission
- months since planning consent
- months since construction started
- number of historical project observations

### Historical comparables

- developer projects observed before the snapshot
- developer operations observed before the snapshot
- smoothed developer completion rate
- technology-region projects observed before the snapshot
- technology-region operations observed before the snapshot
- smoothed technology-region completion rate

## Candidate models

1. **Empirical survival baseline** — smoothed annual hazards by stage and
   technology.
2. **Logistic survival model** — a regularised, one-hot encoded statistical
   baseline.
3. **CatBoost survival challenger** — a nonlinear categorical model intended to
   capture interactions.
4. **Historical base rate** — a constant benchmark used in validation.

A complex candidate is not promoted merely because its ROC-AUC is higher. The
selection rule prioritises temporal-holdout Brier score and rejects models with
worse reliability.

## Validation

Reported measures are:

- ROC-AUC for ranking;
- average precision for rare events;
- Brier score for probability accuracy;
- log loss;
- precision and recall at a 50% threshold;
- calibration bins comparing predicted and observed rates.

The five-year result has particularly limited temporal evidence because only
the oldest source cohorts have five complete years of follow-up.

## External economic and policy context

The app downloads official Bank Rate, CPI and infrastructure construction-cost
history. It also exposes assumptions for policy support, grid delay and new CfD
support.

These inputs are intentionally placed in a separate scenario layer. With only
15 REPD snapshots, a macro variable has only 15 independent time observations,
even if it is duplicated across thousands of project rows. Treating those rows
as independent would create false statistical confidence.

The scenario layer applies bounded log-odds adjustments with greater
sensitivity for early-stage and capital-intensive projects. These coefficients
are transparent stress assumptions, not estimated causal effects.

## Aggregate forecasts

Expected capacity for a group is:

```text
sum(project capacity × project probability)
```

This is an expectation across a portfolio, not a promise that any individual
project will proceed.

## Known limitations

- REPD's minimum inclusion threshold changed in 2021.
- Snapshot dates are irregular.
- Public status definitions and column names changed over time.
- Revised applications and renaming can create matching errors.
- Macroeconomic history uses the latest published statistical vintage.
- Public sources omit private financing, land, supply-chain contracts and
  detailed grid studies.
- The platform is not an investment-grade valuation or investment advice.
