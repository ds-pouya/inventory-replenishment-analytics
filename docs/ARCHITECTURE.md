# Architecture

The pipeline turns M5 sales, calendar, and price files into a validated daily sales
mart, then uses that mart for forecast backtesting and demand diagnostics.

```text
M5 CSV files and source metadata
    -> DuckDB validation and SQL transformations
    -> daily_sales.parquet and a quality profile
    -> rolling-origin candidate forecasts and frozen final evaluation
    -> deterministic inventory-policy simulation
    -> Streamlit demand, forecast, and scenario diagnostics
```

## Technology choices

I chose DuckDB for local CSV processing and SQL transformations. It handles the
source tables without requiring a separate database server. Parquet provides a
compact analytical format that both the forecasting code and dashboard can read.

Python coordinates acquisition, validation, and backtesting. pandas handles the
forecast comparisons and dashboard summaries. Streamlit provides an interactive
interface for exploring demand, forecasts, and policy scenarios. `presentation.py`
aggregates filtered metrics and applies the dashboard’s service-threshold rule. The application
runs locally on macOS without a paid cloud service.

Direct dependencies are pinned in `requirements.txt`; `requirements-lock.txt`
records the installed development environment. The forecasts combine statistical
baselines with calendar-aware ridge regression
implemented using NumPy. No external machine-learning framework is required.

## Data model

| Dataset | Grain |
| --- | --- |
| Daily sales mart | item_id + store_id + date |
| Calendar | unique day key and date |
| Weekly prices | item_id + store_id + wm_yr_wk |
| Validation forecasts | item_id + origin + day_number + model |

The current mart covers one store and department. Item selection uses sales
through day 1801, with item ID as the tie-breaker. Calendar and price keys are
validated before joining, and row counts and unit totals are reconciled afterward.
Missing prices are permitted only on zero-sales rows and counted in the profile.

Source URLs, retrieval time, provider checksums, and SHA-256 fingerprints are stored
with the local raw files. The mart has a separate build configuration and input
fingerprints. Raw and generated data are excluded from Git.

## Forecast evaluation

Four expanding 28-day validation windows follow the initial training period.
Each forecast uses only observations available at its origin. The final 28 days
were evaluated after committing the selection record.
They are now considered inspected for subsequent development.

MAE measures absolute unit error per item-day. Aggregate WAPE divides total
absolute error by total observed units; a zero denominator produces a null score.
These metrics evaluate the selected series, rather than the complete M5 hierarchy.

## Inventory simulation

`simulation.py` replays fixed-cover and order-up-to policies across a lead-time
and starting-stock grid. Historical sales serve as requested units because the
source contains no actual inventory balances or unmet-demand records. The replay
uses the previously evaluated forecast period and is retrospective.

Each ledger tracks receipts, orders, requested/fulfilled/lost units, closing stock,
and outstanding orders. Receipts precede opening reviews and daily demand. Orders
arrive on the order day plus lead time. Daily and cumulative stock/pipeline balances
are enforced. Forecasts stay fixed at day 1913, and safety buffers use earlier
validation errors. Monetary comparisons are outside the current model.

## Reporting extensions

Power BI project/model files and a paginated exception report are planned after
the forecasting and simulation stages. Completion of these artifacts includes
refresh, rendering, and export checks in the target reporting runtime.
