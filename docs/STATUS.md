# Implementation status — 2026-10-15

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
- Twelve synthetic-data tests passed; real-data Streamlit checks passed for the full
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

Twelve automated tests pass. Real-data dashboard checks cover both evaluation
periods, single-product filtering, and empty selections.

## Next milestone

Implement periodic-review inventory simulation and compare a fixed-cover baseline
with an order-up-to policy. Lead times, initial stock, service targets, and event
timing will be documented scenario inputs; outcomes will be labeled as simulated.

The final forecasting period is now inspected. Later comparisons on those days
are retrospective rather than independent final tests. Inventory simulation,
public app deployment, and native BI reports remain future work.
