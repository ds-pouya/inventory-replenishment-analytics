# Project charter

## Audience and outcome

An inventory planner needs an explainable exception list and a comparison of
replenishment policies. The published result should answer which policy performs
best for a stated subset and assumptions, including uncertainty and tradeoffs.

## Scope

- Historical sales diagnostics by item, store, category and day.
- Product segmentation by observed sales value and variability.
- Seasonal-naive baseline, then one justified forecasting improvement.
- Rolling-origin evaluation and a final 28-day period scored after model selection.
- Periodic-review order-up-to policy against a simple fixed-cover baseline.
- Simulated service and inventory outcomes; optional cost comparison only when
  unit-cost, holding-cost and unmet-unit penalty assumptions are documented.

## Boundaries

This independent public-data case study covers demand planning and simulated
inventory policies. The available data does not support actual-stockout detection,
supplier performance, measured procurement savings, or causal price-elasticity
estimates. Production inventory integration is outside the project scope.

## Planned outputs

Demand overview, forecast diagnostics and replenishment scenario pages in Streamlit;
subsequently a verified PBIP/PBIR report/model and RDL exception report. A technical
walkthrough explains data grain, joins, metrics, assumptions and why results differ.

## Acceptance

Completion criteria include a reproducible subset, reconciled joins, backtests
without future-data leakage, baseline comparisons, inventory-flow conservation
checks, source attribution, and a working demonstration. Model improvements are
measured against the baselines. Cost and service comparisons will be reported as
simulation results with their assumptions.
