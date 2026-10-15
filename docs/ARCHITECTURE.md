# Planned architecture

Official CSVs -> immutable local raw files and manifest -> Python/DuckDB profiling
and SQL transforms -> partitioned analytical Parquet -> forecasts and policy
simulation -> Streamlit; later validated Power BI model/report and RDL.

## Intended analytical grains

- Daily sales: item_id + store_id + date.
- Calendar: date, with unique source day key and week identifier.
- Weekly price: item_id + store_id + wm_yr_wk.
- Forecast: item_id + store_id + origin + target_date + model_version.
- Simulation: scenario_id + policy_id + item_id + store_id + date + run_id.

Record train cutoff, source manifest hash, scenario config and seed with each run.
Keep forecasts made at each origin immutable; do not train on future sales or
choose simulation policy parameters using the final evaluation period.

## Implementation choices

Mac-first: Python, DuckDB, Parquet, pandas, scikit-learn and Streamlit. Exact versions
and optional forecasting libraries will be selected and pinned during implementation.
Use straightforward SQL here; the bike-share project owns the full dbt/orchestration
showcase. No paid cloud service is required for the initial implementation.

## Planned metrics

Forecast: MAE and aggregate WAPE, explicitly handling zero denominators. Hierarchical
WRMSSE is optional and must not be claimed from a simple unweighted slice score.
Simulation: unit fill rate = fulfilled units / requested scenario units; mean ending
inventory; unmet units; orders placed. Specify receipt/order timing and lost-sales
versus backorder behavior. Requested scenario units initially replay held-out sales;
this is a proxy, not measured unconstrained demand. Cost metrics remain disabled
until their inputs are documented. Reconcile opening + receipts - fulfilled = ending.

## Validation boundary

Python checks and JSON/XML schemas do not prove Power BI/RDL rendering or refresh.
Mark native reports unverified until opened, refreshed, and visually reviewed in
Power BI or the appropriate service/runtime. Do not publish placeholder report files.
