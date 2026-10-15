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
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m streamlit run app/streamlit_app.py
```

The first command creates an isolated environment, not a global installation.
Acquisition needs network access; subsequent builds use the local files. The
university mirror was explicitly selected for local analysis on 2026-10-15.
No Kaggle key is needed. Downloads are approximately 326 MB in total.

The downloader verifies the provider's MD5 and records local SHA-256 hashes,
URLs, sizes and retrieval time under ignored `data/raw/m5/`. MD5 here is an
integrity check, not an authenticity guarantee. Existing mismatched files cause
a failure rather than an overwrite. An interrupted `.part` download restarts.

The build validates input keys, sales ranges and joins before replacing the mart.
Outputs are reproducible for identical source bytes and configuration; timestamps
will differ. Missing prices are allowed only on zero-sales rows and counted in
the profile. No unpriced positive sales silently enter reported sales value.

The application is read-only. It displays the training interval, not the final
holdout, and reads local generated Parquet. It is not yet deployed publicly.

## Output files

- `data/processed/daily_sales.parquet`: selected item-store-day observations.
- `data/processed/profile.json`: input fingerprints and aggregate quality profile.
- `data/processed/build_config.json`: configuration used to build this mart.
- `data/processed/validation_forecasts.parquet`: forecasts/actuals by model and origin.
- `data/processed/validation_metrics.json`: per-window MAE and aggregate WAPE.

These files are ignored by Git. Publish reviewed aggregate findings separately;
do not commit the underlying source records as a dashboard deployment shortcut.
