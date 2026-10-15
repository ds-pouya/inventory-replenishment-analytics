# Inventory Replenishment Analytics

A portfolio project connecting retail demand forecasting to inventory decisions.

**Status:** ingestion, source validation, sales-mart generation, two forecast
baselines, and a local Streamlit demand overview are implemented. See
[run status](docs/STATUS.md) for completed real-data checks and current limitations.
Inventory simulation and native Power BI/RDL artifacts remain future work.

## Business decision

Help an inventory planner prioritize item-store combinations and compare replenishment
policies under explicit lead-time, starting-stock, and cost assumptions.

M5 provides historical sales, prices, product/store structure and calendar context.
Inventory outcomes will be **simulated**, because actual inventory and supply records
are absent. Zero sales do not prove a stockout; sales are not unconstrained demand.

## Planned approach

1. Acquire and profile official M5 files; document provenance and reuse terms.
2. Build a deterministic small subset and reconcile daily sales/price/calendar joins.
3. Establish seasonal-naive forecasts, then evaluate alternatives chronologically.
4. Simulate inventory policies with assumptions available at each decision date.
5. Build a Streamlit decision tool; add Power BI and paginated reporting after
   validating those artifacts in their respective runtimes.
6. Publish measured findings, screenshots and a concise explanation guide.

## Start here

- [Project charter](docs/PROJECT_CHARTER.md)
- [Data source and acquisition plan](docs/DATA_SOURCES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Milestones](docs/MILESTONES.md)
- Portfolio roadmap: sibling `PORTFOLIO_PROJECT_ROADMAP.txt` in the local workspace.

## Layout

```text
config/          versioned source selection and scenario assumptions
scripts/         acquisition, build and baseline backtest entrypoints
src/inventory_analytics/  validated transformations and forecast baselines; simulation planned
sql/             future source-to-mart SQL
notebooks/       exploratory work; production logic belongs in src/ or sql/
app/             local Streamlit demand and forecast diagnostics
reports/         future Power BI project and paginated RDL source
outputs/         local generated artifacts, excluded from Git
assets/          reviewed screenshots and diagrams for publication
tests/           future meaningful data/model/simulation checks
```

## Run locally

See [setup instructions](docs/SETUP.md) for acquisition and environment details.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python scripts/download_data.py
.venv/bin/python scripts/build_data.py
.venv/bin/python scripts/backtest.py
.venv/bin/python -m streamlit run app/streamlit_app.py
```

Run checks with `.venv/bin/python -m unittest discover -s tests -v`.
Source: [University of Nicosia M5 mirror](https://zenodo.org/records/10203108),
used locally with documented provenance. No raw source data is committed.
See the [explanation guide](docs/EXPLANATION_GUIDE.md) for model and metric reasoning.
