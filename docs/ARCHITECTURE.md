# Architecture

The pipeline turns M5 sales, calendar, and price files into a validated daily sales
mart, then uses that mart for forecast backtesting and demand diagnostics.

```text
M5 CSV files and source metadata
    -> DuckDB validation and SQL transformations
    -> daily_sales.parquet and a quality profile
    -> rolling-origin baseline forecasts
    -> Streamlit demand and forecast diagnostics
```

## Technology choices

I chose DuckDB for local CSV processing and SQL transformations. It handles the
source tables without requiring a separate database server. Parquet provides a
compact analytical format that both the forecasting code and dashboard can read.

Python coordinates acquisition, validation, and backtesting. pandas handles the
forecast comparisons and dashboard summaries. Streamlit provides an interactive
interface for exploring demand and comparing forecasts. The initial application
runs locally on macOS without a paid cloud service.

Direct dependencies are pinned in `requirements.txt`; `requirements-lock.txt`
records the installed development environment. The current forecasts use simple
statistical baselines and do not require a machine-learning framework.

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
are reserved for evaluation after model selection.

MAE measures absolute unit error per item-day. Aggregate WAPE divides total
absolute error by total observed units; a zero denominator produces a null score.
These metrics evaluate the selected series, rather than the complete M5 hierarchy.

## Inventory simulation design

The next stage will compare replenishment policies using scenario-specific lead
times, initial stock, and service targets. Held-out sales will act as a demand
proxy because the source contains no inventory balances or unmet-demand records.

The simulation will track receipts, fulfilled units, unmet units, orders, and ending
stock. Its accounting identity is opening stock + receipts - fulfilled units =
ending stock. Event timing and lost-sales behavior will be defined before policy
comparisons. Monetary comparisons depend on documented cost assumptions.

## Reporting extensions

Power BI project/model files and a paginated exception report are planned after
the forecasting and simulation stages. Completion of these artifacts includes
refresh, rendering, and export checks in the target reporting runtime.
