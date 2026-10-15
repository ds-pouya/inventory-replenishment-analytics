"""Read-only demand diagnostics; no simulated inventory outcomes yet."""
from pathlib import Path
import json
import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Inventory | Demand diagnostics", layout="wide")
st.title("Inventory planning")
st.caption("M5 retail case study · Demand diagnostics · Milestone 2")
st.info("Observed sales are fulfilled units, not unconstrained demand. Inventory and supplier data are unavailable; replenishment simulation is a later milestone.")
mart = ROOT / "data/processed/daily_sales.parquet"
if not mart.exists():
    st.warning("No data mart yet. Run python scripts/download_data.py, then python scripts/build_data.py.")
    st.stop()
profile = json.loads((mart.parent / "profile.json").read_text())
@st.cache_data
def load(path, modified):
    with duckdb.connect() as con:
        return con.execute("SELECT * FROM read_parquet(?)", [path]).df()
df = load(str(mart), mart.stat().st_mtime_ns)
origin_dates = dict(zip(df.day_number, df.date.dt.strftime("%Y-%m-%d")))
# Keep evaluation outcomes out of exploratory charts by default.
cutoff = json.loads((mart.parent / "build_config.json").read_text())["subset"]["selection_end_day"]
df = df[df.day_number <= cutoff]
st.caption(f"Training history only (through day {cutoff}). Validation and final holdout are excluded from this overview.")
with st.sidebar.expander("Filter products", expanded=False):
    items = st.multiselect("Products", sorted(df.item_id.unique()), default=sorted(df.item_id.unique()))
if not items:
    st.warning("Select at least one product.")
    st.stop()
view = df[df.item_id.isin(items)]
def compact(value):
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"
a,b,c = st.columns(3)
a.metric("Selected products", len(items))
b.metric("Observed units", compact(view.units.sum()))
c.metric("Sales value (USD)", "$" + compact(view.sales_value.sum()))
st.caption("Sales value = units × reported selling price; this is not profit or inventory cost.")
st.subheader("Weekly observed sales")
st.line_chart(view.set_index("date").resample("W").units.sum())
st.subheader("Product priorities by training sales")
summary = view.groupby("item_id").agg(units=("units","sum"), sales_value=("sales_value","sum"),
    zero_sales_share=("units", lambda x: (x == 0).mean())).sort_values("sales_value",ascending=False)
st.dataframe(summary, width="stretch")
with st.expander("Data quality and scope"):
    st.write(profile["checks"])
    st.write(f"Unpriced zero-sales records across all days: {profile['unpriced_zero_sales_rows']:,}. These do not contribute to sales value.")
    st.write("Active products at CA_1 / FOODS_3 only; not representative of all retail products. University Zenodo mirror used locally; raw source data is excluded from Git.")

metrics_path = mart.parent / "validation_metrics.json"
if metrics_path.exists():
    st.subheader("Forecast baseline comparison — full selected cohort")
    import pandas as pd
    metrics = pd.DataFrame(json.loads(metrics_path.read_text()))
    metrics["Forecast origin"] = metrics.origin.map(origin_dates)
    metrics = metrics.rename(columns={"model": "Model", "mae": "MAE (units)", "wape": "WAPE", "actual_units": "Actual units", "observations": "Item-days"})
    st.dataframe(metrics[["Forecast origin", "Model", "MAE (units)", "WAPE", "Actual units", "Item-days"]], width="stretch")
    st.caption("Four historical validation windows. MAE is units per item-day; WAPE is a fraction. Final holdout evaluation has not been run.")
    forecast_path = mart.parent / "validation_forecasts.parquet"
    if forecast_path.exists():
        st.subheader("Product forecast diagnostics")
        product = st.selectbox("Product to inspect", items)
        with duckdb.connect() as con:
            history = con.execute("SELECT * FROM read_parquet(?) WHERE item_id = ? ORDER BY day_number", [str(forecast_path), product]).df()
        comparison = history.pivot(index="day_number", columns="model", values="prediction")
        actuals = history.drop_duplicates("day_number").set_index("day_number").actual
        comparison["Observed sales"] = actuals
        comparison.index = pd.to_datetime([origin_dates[day] for day in comparison.index])
        comparison.index.name = "Date"
        st.line_chart(comparison.rename(columns={"seasonal_naive_7": "Previous-week pattern", "mean_28": "Recent daily average"}))
        st.caption("Forecasts are issued at each 28-day window's start; later observations inside that window are not used to update predictions.")
