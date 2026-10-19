# Local setup (macOS)

Python 3.13 was used for the first development environment. Commands below run
from the project root. The lock file records the tested macOS environment;
other platforms may need their own dependency resolution.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/download_data.py
.venv/bin/python scripts/build_data.py
.venv/bin/python scripts/backtest.py
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/simulate.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m streamlit run app/streamlit_app.py
```

The virtual environment keeps dependencies isolated. Acquisition requires network
access; subsequent builds use local files. The university mirror requires no
Kaggle key. The three source downloads total approximately 326 MB.

The downloader verifies the provider's MD5 and records local SHA-256 hashes,
URLs, sizes and retrieval time under ignored `data/raw/m5/`. MD5 here is an
integrity check, not an authenticity guarantee. Existing mismatched files cause
a failure rather than an overwrite. An interrupted `.part` download restarts.

The build validates input keys, sales ranges and joins before replacing the mart.
Outputs are reproducible for identical source bytes and configuration; timestamps
will differ. Missing prices are allowed only on zero-sales rows and counted in
the profile. No unpriced positive sales silently enter reported sales value.

The demand overview displays the training interval. Forecast diagnostics offer
validation and final-holdout views. The application reads local Parquet and is
not yet deployed publicly. Final evaluation requires the committed selection
fingerprints; a regenerated mart with different bytes will fail that check.
See `docs/FORECASTING.md` for the evaluation lifecycle.

## Output files

- `data/processed/daily_sales.parquet`: selected item-store-day observations.
- `data/processed/profile.json`: input fingerprints and aggregate quality profile.
- `data/processed/build_config.json`: configuration used to build this mart.
- `data/processed/validation_forecasts.parquet`: forecasts/actuals by model and origin.
- `data/processed/validation_metrics.json`: per-window MAE and aggregate WAPE.

These generated files are ignored by Git. Published results contain aggregate
findings; the source records remain local.

Additional forecasting outputs include `forecast_selection.json`,
`zero_sales_diagnostics.json`, `final_forecasts.parquet`, and `final_metrics.json`
in `data/processed/`. The tracked selection record lives in
`docs/FORECAST_SELECTION.json`; aggregate findings are in `docs/FORECAST_RESULTS.md`.

## Inventory replay outputs

`simulate.py` reads `config/scenarios.toml`, the frozen forecast selection, the
sales mart, the source calendar, and pre-replay validation errors. It writes:

- `simulation_daily.parquet`: the per-product, per-policy daily accounting ledger.
- `simulation_products.parquet`: product metrics for each policy and scenario.
- `simulation_assumptions.parquet`: initial stock, historical means, and buffers.
- `simulation_summary.json`: aggregate metrics, configuration, and input/code hashes.

These outputs remain under ignored `data/processed/`. The dashboard's scenario
selector compares the precomputed grid; changing the configuration requires
rerunning `simulate.py`. No live policy optimization is performed.

## Native report sources

After the simulation, generate local extracts and reporting definitions:

```bash
.venv/bin/python scripts/build_native_reports.py
.venv/bin/python scripts/validate_native_reports.py
```

The builder checks every exported scenario-policy comparison against the published
simulation results and writes a local reconciliation record under `outputs/`.
The schema checker needs internet access on its first run and `xmllint` (available
on macOS). Generated CSV data stays under ignored `data/processed/native/`.
No Power BI runtime is installed by these commands. Follow the
[Power BI](../reports/powerbi/README.md) and [RDL](../reports/paginated/README.md)
acceptance procedures before claiming native runtime validation. The builder
regenerates report definitions; preserve any manual report edits first.

## Synthetic demo without source acquisition

Run `.venv/bin/python -m streamlit run app/demo_app.py` after installing the locked
dependencies. This always uses the committed `data/demo/` bundle and never falls
back to local M5 data. Regeneration is optional: `python scripts/build_demo.py`.
See [deployment and validation](DEPLOYMENT.md).
