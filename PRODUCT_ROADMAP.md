# Product and Commercial Roadmap

## Positioning

Do not sell “an AI probability”. Sell a faster way to identify which UK
renewable projects changed, why they changed and which projects require human
review.

## Initial users

1. Small renewable developers and project originators
2. Energy and engineering consultancies
3. Infrastructure researchers and recruitment teams
4. Local supply-chain businesses tracking upcoming work

## Product ladder

### Free public product

- Project explorer
- Research forecasts
- Methodology and Trust Centre
- A limited number of project briefs

### Professional product

- Saved portfolios
- Data-change alerts
- Batch export
- Scenario comparison
- Project and regional briefing packs
- API access

### Team or advisory product

- Private watchlists
- Custom data overlays
- Reviewed project briefs
- Organisation-specific scoring
- Scheduled portfolio reports

## Next validation steps

- Interview at least ten potential users before building billing.
- Ask what project change currently causes the most manual work.
- Test a paid pilot around alerts and briefing, not around model accuracy.
- Record whether users act on planning, CfD, grid or developer changes.
- Avoid price optimisation until one workflow repeatedly saves users time.

## Technical milestones

1. Recover more REPD snapshots and audit project matching.
2. Add official NESO connection-register matching.
3. Add CfD award and delivery-year matching.
4. Add persistent authenticated watchlists.
5. Add scheduled change detection and email alerts.
6. Add an API only after a stable data contract exists.
7. Reassess model promotion after genuinely later holdouts become available.

## Portfolio narrative

The strongest interview story is not “I used CatBoost”. It is:

> I found that an apparently accurate model had an all-positive temporal test
> set. I rebuilt the labels as a censored survival problem, created strict
> holdouts, rejected a more complex model when it failed reliability tests and
> exposed the evidence in a public Trust Centre.
