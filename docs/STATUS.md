# Implementation status — 2026-10-19

## Completed and verified locally

- Downloaded the three M5 inputs from the university Zenodo mirror;
  provider size/MD5 checks passed and SHA-256/source metadata recorded locally.
- Profiled 30,490 sales series, 1,969 calendar rows and 6,841,121 weekly prices.
- Built a 50-product CA_1 / FOODS_3 mart with 97,050 item-day observations,
  covering 2011-01-29 through 2016-05-22.
- Reconciled joined row counts and unit totals; no missing prices on positive sales.
- Found 6,111 unpriced zero-sales rows; they remain explicit missing
  prices, not zero-priced merchandise or observed stockouts.
- Ran two baseline forecasts and a calendar-aware regression across four validation windows.
- Twenty-one synthetic-data tests passed; real-data Streamlit checks passed for the full
  cohort, empty selection and a single product. Dependencies pass pip check.
- Started local preview at http://127.0.0.1:8503.

## Forecasting milestone completed

Three models have been compared: previous-week pattern, recent 28-day average,
and calendar-aware ridge regression. Selection used pooled validation MAE and
was frozen in commit `212c40a` before final scoring.

Calendar ridge won validation (MAE 6.101) but scored 6.060 on the final holdout,
compared with 5.911 for the recent average. The selected model remains fixed.
[Forecasting results](FORECAST_RESULTS.md) describe all scores and limitations;
[methodology](FORECASTING.md) describes the reproducible selection and evaluation.

Training-only diagnostics found at least one 28-day zero-sales run in 36 products.
These observations do not identify stockouts. The dashboard now displays all
three forecasts, validation/final scores, and zero-sales diagnostics.

The forecasting milestone passed twelve automated tests and dashboard checks for
both evaluation periods, single-product filtering, and empty selections.

## Inventory simulation milestone completed

Fixed-cover and order-up-to policies have been replayed across nine scenarios.
All 25,200 daily ledger rows pass stock, demand, and pipeline accounting checks;
a deterministic rerun produced the same summary. Twenty-one automated tests pass,
and scenario/product/empty-selection dashboard checks pass.

In the base scenario, order-up-to holds 17.7% less average closing inventory,
but simulated unit fill falls from 94.83% to 93.88%. The comparison shows a tradeoff,
not a financial saving or a policy that dominates on both measures. These results
use historical sales as a proxy and hypothetical starting stock and lead times.
[Simulation results](SIMULATION_RESULTS.md) report the full sensitivity grid.

## Decision dashboard milestone completed

The application has four views: Overview, Inventory, Demand, and Forecasts.
Decision summaries respect a chosen fill-rate threshold and identify tradeoffs
without assigning monetary benefits. Scenario comparisons, product exceptions,
aggregate downloads, and forecast/demand drill-downs share consistent cohort filters.
Undefined service and stock changes are handled without false recommendations.

The light theme and chart labels have been reviewed across all four desktop views.
All 31 local checks pass: 28 unit checks and three dashboard integration checks.
[Dashboard guide](DASHBOARD.md) documents navigation, filters, and interpretation.

## Publication package completed

The repository now leads with the business question, inventory tradeoff, forecast
comparison, and actual dashboard captures. Four viewport screenshots have been
visually checked; their context, dimensions, and hashes are recorded under
`assets/screenshots/`. The demand trend now includes years on its date axis.

The [gallery](DASHBOARD_GALLERY.md) provides static previews without installation.
The [technical walkthrough](TECHNICAL_WALKTHROUGH.md) traces source grain, join
validation, chronological selection, inventory accounting, and the dashboard demo.
The materials retain the difference between observed sales and simulated inventory.
All 31 local checks pass. A separate temporary rebuild from the verified raw inputs
passed frozen forecast evaluation and reproduced all 18 scenario-policy summaries.

## Native reporting source phase

Added a PBIP project with two PBIR pages, a TMSL semantic model, and a parameterized
RDL inventory exception report. A repeatable build creates five local CSV tables
from the verified simulation ledger. All 18 scenario-policy pairs reconcile with
the published unit-fill, average-stock, and unmet-unit results.

Fifteen report/project JSON documents pass Microsoft's public schemas; the RDL
passes Microsoft's 2016/01 XSD. All 35 project tests and pip check pass.
[Native validation record](../reports/VALIDATION.md) distinguishes these source
checks from pending runtime validation. Model load, DAX and Power Query execution,
report rendering, RDL connections, pagination, and exports remain unverified.
M7 remains open until those checks can run in Power BI Desktop/Report Builder or
an appropriate service environment. The Python app remains the demonstrated
application; public hosting is a separate deployment step.

## Public demo package

A separate public entry point, `app/demo_app.py`, reads a checked-in synthetic
bundle for 24 invented products. It has no runtime M5 data dependency, and every
view displays its synthetic provenance. The generator uses the existing pipeline
in a disposable directory, leaving M5 outputs and selection fingerprints intact.

All 38 local checks pass, including a clean-copy demo test without M5 data, bundle
hashes, navigation, filters, forecasts, and inventory accounting. A read-only
GitHub Actions workflow runs project checks on clean Linux checkouts.
The [deployment guide](DEPLOYMENT.md) records the repository, entry point, Python
version, and public smoke-test procedure. Hosting and a verified live URL remain
pending; M8 is not yet complete.
