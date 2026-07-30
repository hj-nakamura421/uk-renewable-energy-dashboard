# Model Card — Forecasting Model v2

## Intended use

Portfolio research, engineering exploration and demonstration of a
leakage-aware public-data forecasting workflow.

## Not intended for

- investment decisions;
- project valuation;
- lending or insurance decisions;
- claims about confidential developer capability;
- automatic approval or rejection of infrastructure projects.

## Training data

The packaged release contains 103,579 project-snapshot rows, 19,145 linked
project keys and 15 REPD snapshots from September 2019 to May 2026.

The generated metrics file is the authoritative record for the exact packaged
model and includes the training timestamp, event counts and holdout results.

## Output

For each currently active project:

- probability of operation within 2, 3 and 5 years;
- probability-weighted capacity;
- public-data confidence category;
- positive public-data signals;
- risk and missing-evidence signals.

## Candidate-selection policy

The pipeline compares an empirical survival baseline, logistic survival model
and CatBoost challenger against the historical base rate. The final model is
selected using temporal-holdout Brier score. Complexity provides no automatic
promotion advantage.

## Current release status

**Research only.**

The corrected holdouts show material temporal drift and insufficient evidence
for decision-grade probability calibration. The CatBoost challenger is kept as
an auditable comparison but is not deployed as the primary forecast.

## Main risks

- sparse independent time history;
- source threshold and schema changes;
- imperfect project entity resolution;
- rare positive outcomes;
- omitted private project information;
- temporal and policy regime shifts;
- latest-vintage macro revisions.

## Monitoring

Every rebuild writes:

- `data/processed/model_metrics.json`
- `data/processed/data_quality_report.json`
- `data/processed/external_metadata.json`

The Trust Centre renders these artifacts directly.

## Promotion criteria

The model should remain research-only until:

1. more independent historical snapshots are recovered;
2. later rolling-origin tests contain both outcomes;
3. the selected model beats the base-rate Brier score consistently;
4. calibration is acceptable by technology and region;
5. entity-resolution error is manually audited;
6. scenario assumptions are reviewed with a domain expert.
