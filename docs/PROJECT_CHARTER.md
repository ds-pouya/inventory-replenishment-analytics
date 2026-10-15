# Project charter

## Audience and outcome

An inventory planner needs an explainable exception list and a comparison of
replenishment policies. The published result should answer which policy performs
best for a stated subset and assumptions, including uncertainty and tradeoffs.

## Scope

- Historical sales diagnostics by item, store, category and day.
- Product segmentation by observed sales value and variability.
- Seasonal-naive baseline, then one justified forecasting improvement.
- Rolling-origin evaluation and a final untouched 28-day evaluation period.
- Periodic-review order-up-to policy against a simple fixed-cover baseline.
- Simulated service and inventory outcomes; optional cost comparison only when
  unit-cost, holding-cost and unmet-unit penalty assumptions are documented.

## Boundaries

No actual-stockout detection, supplier performance, measured procurement savings,
causal price-elasticity claims, or production inventory integration. No duplication
of the separate procurement, solar, credit-risk or bike-share portfolio projects.
No claimed customer or employer engagement: this is an independent public-data case.

## Planned outputs

Demand overview, forecast diagnostics and replenishment scenario pages in Streamlit;
subsequently a verified PBIP/PBIR report/model and RDL exception report. A technical
walkthrough explains data grain, joins, metrics, assumptions and why results differ.

## Acceptance

Reproducible subset, join reconciliation, leakage-safe backtests, honest baseline
comparison, inventory-flow conservation checks, source/assumption attribution,
a working demo and screenshots. Improvement is a hypothesis, not a requirement to
manufacture a positive finding. Publish costs and service changes as simulation.
