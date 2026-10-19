"""Interactive retail planning case study with consistent cohort-level metrics."""
from pathlib import Path
import json
import sys

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.presentation import (
    MODEL_LABELS, POLICY_LABELS, decision_summary, forecast_metrics, policy_metrics,
)

st.set_page_config(page_title='Inventory decisions | Retail analytics', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
.block-container {padding-top:4rem; padding-bottom:2rem; max-width:1280px;}
h1 {font-size:2.35rem!important; letter-spacing:-.055rem;}
h2 {font-size:1.45rem!important; letter-spacing:-.025rem;}
h3 {font-size:1.12rem!important;}
[data-testid="stMetricValue"] {font-size:1.9rem;}
[data-testid="stMetricLabel"] {font-size:.85rem;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px;}
@media(max-width:700px) {.block-container {padding-left:1rem; padding-right:1rem;} h1 {font-size:1.9rem!important;}}
</style>''', unsafe_allow_html=True)

OUT = ROOT / 'data/processed'
required = ['daily_sales.parquet', 'profile.json', 'build_config.json',
            'simulation_summary.json', 'simulation_daily.parquet',
            'validation_forecasts.parquet', 'final_forecasts.parquet', 'zero_sales_diagnostics.json']
missing = [name for name in required if not (OUT / name).exists()]
if missing:
    st.title('Inventory decisions')
    st.info('Build the local analysis to explore the dashboard.')
    with st.expander('Local setup', expanded=True):
        st.code('python scripts/download_data.py\npython scripts/build_data.py\npython scripts/backtest.py\npython scripts/evaluate.py\npython scripts/simulate.py', language='shell')
        st.caption('Missing outputs: ' + ', '.join(missing))
    st.stop()


@st.cache_data
def load(name, modified):
    with duckdb.connect() as con:
        return con.execute('SELECT * FROM read_parquet(?)', [str(OUT / name)]).df()


def data(name):
    return load(name, (OUT / name).stat().st_mtime_ns)


def compact(value):
    return f'{value / 1_000_000:.2f}M' if abs(value) >= 1_000_000 else f'{value / 1_000:.1f}K' if abs(value) >= 1_000 else f'{value:,.0f}'


COLORS = ['#52677E', '#0F766E']
POLICY_COLOR = alt.Color('Policy:N', scale=alt.Scale(domain=list(POLICY_LABELS.values()), range=COLORS), legend=alt.Legend(title=None, orient='bottom'))


def chart(frame, y, label, group='Policy'):
    color = POLICY_COLOR if group == 'Policy' else alt.Color(f'{group}:N', legend=alt.Legend(title=None, orient='bottom'))
    return alt.Chart(frame).mark_line(strokeWidth=2.3).encode(
        x=alt.X('date:T', title=None), y=alt.Y(f'{y}:Q', title=label), color=color,
        tooltip=[alt.Tooltip('date:T', title='Date'), alt.Tooltip(f'{group}:N'), alt.Tooltip(f'{y}:Q', title=label, format=',.1f')],
    ).properties(height=260)


sales = data('daily_sales.parquet')
build = json.loads((OUT / 'build_config.json').read_text())
training = sales[sales.day_number <= build['subset']['selection_end_day']]
simulation = json.loads((OUT / 'simulation_summary.json').read_text())
all_replay = data('simulation_daily.parquet')
base = simulation['scenario_config']['scenario']
sensitivity = simulation['scenario_config']['sensitivity']
with st.sidebar:
    st.header('Planning context')
    st.caption('CA_1 store · FOODS_3 department')
    leads = sorted(set(sensitivity['lead_time_days'] + [base['lead_time_days']]))
    covers = sorted(set(sensitivity['initial_stock_cover_days'] + [base['initial_stock_cover_days']]))
    lead = st.selectbox('Supplier lead time (days)', leads, index=leads.index(base['lead_time_days']), key='lead')
    cover = st.selectbox('Initial stock cover (days)', covers, index=covers.index(base['initial_stock_cover_days']), key='cover')
    threshold = st.slider('Planning fill-rate threshold (%)', min_value=80., max_value=100., value=95., step=.5, key='threshold') / 100
    st.caption('A comparison preference; it does not resize the simulation’s safety buffer.')
    with st.expander('Product selection'):
        items = st.multiselect('Products', sorted(training.item_id.unique()), default=sorted(training.item_id.unique()), key='products')
    st.caption('Scenario inputs affect Overview and Inventory. Product selection applies to all views. Weekly reviews; no monetary objective.')

st.caption('RETAIL OPERATIONS / INVENTORY PLANNING')
active_view = st.session_state.get('page', 'Overview')
titles = {'Overview': 'Balance service and stock', 'Inventory': 'Explore inventory scenarios',
          'Demand': 'Understand sales patterns', 'Forecasts': 'Evaluate forecast evidence'}
subtitles = {'Overview': 'Compare replenishment policies and inspect the service–inventory tradeoff.',
             'Inventory': 'See how supplier lead time and starting stock change simulated service.',
             'Demand': 'Profile fulfilled sales across the training period.',
             'Forecasts': 'Compare fixed forecasting candidates across historical evaluation windows.'}
st.title(titles[active_view])
st.write(subtitles[active_view])
if not items:
    st.warning('Select at least one product in Planning context to continue.')
    st.stop()
scenario_id = f"L{lead}_R{base['review_period_days']}_I{cover}"
replay = all_replay[(all_replay.scenario_id == scenario_id) & all_replay.item_id.isin(items)]
metrics = policy_metrics(replay)
insight = decision_summary(metrics, threshold)
start, end = replay.date.min().strftime('%d %b %Y'), replay.date.max().strftime('%d %b %Y')
if active_view in ('Overview', 'Inventory'):
    st.caption(f'{len(items)} products · Lead {lead} days · Initial cover {cover} days · Replay {start} – {end}')
else:
    st.caption(f'{len(items)} products · CA_1 store · FOODS_3 department')
page = st.radio('Explore the analysis', ['Overview', 'Inventory', 'Demand', 'Forecasts'], horizontal=True, key='page', label_visibility='collapsed')
if page in ('Overview', 'Inventory'):
    st.caption('SIMULATED INVENTORY · Historical sales proxy demand; stock and supplier inputs are hypothetical.')
elif page == 'Demand':
    st.caption('OBSERVED SALES · Fulfilled transactions do not measure unconstrained demand.')
else:
    st.caption('FORECAST BACKTEST · Product filters update scores; model selection remains frozen.')


def comparison_table():
    frame = metrics.copy()
    frame['Policy'] = frame.policy.map(POLICY_LABELS)
    frame['Fill rate (%)'] = frame.unit_fill_rate * 100
    frame = frame.rename(columns={'average_ending_inventory': 'Mean closing stock', 'lost_units': 'Unmet units',
        'order_count': 'Orders', 'ending_stock': 'Final on-hand', 'ending_on_order': 'Final on-order'})
    return frame[['Policy', 'Fill rate (%)', 'Mean closing stock', 'Unmet units', 'Orders', 'Final on-hand', 'Final on-order']].round(2)


if page == 'Overview':
    with st.container(border=True):
        st.subheader(insight['title'])
        st.write(insight['detail'])
    left, right = st.columns(2)
    left.metric('Average stock change', f"{insight['stock_change_pct']:+.1f}%" if insight['stock_change_pct'] is not None else 'N/A', help='Order-up-to versus fixed cover. Based on mean closing on-hand units.')
    right.metric('Fill-rate change', f"{insight['fill_change_pp']:+.2f} pp" if insight['fill_change_pp'] is not None else 'N/A', help='Order-up-to minus fixed cover, in percentage points.')
    st.caption('Both changes compare order-up-to with the fixed-cover baseline for the current selection.')
    st.subheader('The policy tradeoff')
    st.dataframe(comparison_table(), hide_index=True, width='stretch', height=145)
    st.subheader('How stock moves through the replay')
    daily = replay.groupby(['date', 'policy'], as_index=False).ending_stock.sum()
    daily['Policy'] = daily.policy.map(POLICY_LABELS)
    st.altair_chart(chart(daily, 'ending_stock', 'Closing stock (units)'), use_container_width=True)
    with st.expander('What this decision does—and does not—show'):
        st.write('The comparison identifies the lowest-stock displayed policy meeting the chosen fill-rate threshold. It does not optimize costs or establish real retailer savings. Different lead times and starting-stock assumptions can change the ranking.')
        st.write('Forecasts remain fixed at the replay start. The 95% nominal safety-buffer parameter uses approximate error assumptions and does not guarantee 95% fill. The replay has no warm-up and starts with no supplier pipeline.')

elif page == 'Inventory':
    st.subheader('Inventory scenarios')
    st.write('Inspect the current policy pair, then compare all nine lead-time and starting-stock combinations.')
    table = comparison_table()
    st.dataframe(table, hide_index=True, width='stretch')
    st.download_button('Download policy comparison', table.to_csv(index=False), file_name=f'inventory_{scenario_id}_summary.csv', mime='text/csv')
    grid = []
    for (sid, policy), group in all_replay[all_replay.item_id.isin(items)].groupby(['scenario_id', 'policy']):
        row = policy_metrics(group).iloc[0].to_dict()
        l, r, i = [int(value[1:]) for value in sid.split('_')]
        grid.append({'Scenario': f'Lead {l}d / Cover {i}d', 'Lead days': l, 'Initial cover days': i,
            'Policy': POLICY_LABELS[policy], 'Mean stock': row['average_ending_inventory'],
            'Fill rate (%)': row['unit_fill_rate'] * 100 if pd.notna(row['unit_fill_rate']) else None})
    grid = pd.DataFrame(grid)
    st.subheader('Service versus inventory across assumptions')
    scatter = alt.Chart(grid).mark_circle(size=110, opacity=.85).encode(
        x=alt.X('Mean stock:Q', title='Average closing stock (units)'),
        y=alt.Y('Fill rate (%):Q', scale=alt.Scale(domain=[0, 100]), title='Simulated unit fill rate (%)'),
        color=POLICY_COLOR, tooltip=['Scenario:N', 'Policy:N', alt.Tooltip('Mean stock:Q', format=',.1f'), alt.Tooltip('Fill rate (%):Q', format='.2f')],
    ).properties(height=290)
    threshold_rule = alt.Chart(pd.DataFrame({'Planning threshold (%)': [threshold * 100]})).mark_rule(
        color='#B7791F', strokeDash=[5, 4]).encode(y='Planning threshold (%):Q', tooltip=[alt.Tooltip('Planning threshold (%):Q', format='.1f')])
    st.altair_chart(scatter + threshold_rule, use_container_width=True)
    st.caption(f'Dashed line: {threshold:.1%} planning threshold. Each point is one policy/scenario pair.')
    with st.expander('All scenario results'):
        st.dataframe(grid.sort_values(['Lead days', 'Initial cover days', 'Policy']).round(2), hide_index=True, width='stretch')
    st.subheader('Product-level service exceptions')
    exceptions = []
    for (item, policy), group in replay.groupby(['item_id', 'policy']):
        row = policy_metrics(group).iloc[0]
        if row.lost_units:
            exceptions.append({'Product': item, 'Policy': POLICY_LABELS[policy], 'Unmet units': int(row.lost_units),
                               'Fill rate (%)': 100 * row.unit_fill_rate})
    if exceptions:
        st.dataframe(pd.DataFrame(exceptions).sort_values('Unmet units', ascending=False).round(2), hide_index=True, width='stretch')
    else:
        st.success('No unmet units in this replay selection.')
    with st.expander('Event sequence and assumptions'):
        st.write('Daily sequence: receipts → opening review and orders → demand fulfillment → closing stock. Orders placed on day t arrive on t + lead time. Lost units are not backordered; final on-order units include deliveries after the replay ends.')
        st.write('Fixed cover orders a constant quantity every review. Order-up-to accounts for available stock and orders in transit, using calendar forecasts plus an approximate buffer. This compares policy bundles, not the isolated effect of one component.')
        st.caption(simulation['checks'])

elif page == 'Demand':
    view = training[training.item_id.isin(items)]
    st.subheader('Observed demand patterns')
    st.caption(f"Training history only · {view.date.min():%d %b %Y} – {view.date.max():%d %b %Y}. Validation and final-period sales are excluded.")
    left, right = st.columns(2)
    left.metric('Fulfilled sales units', compact(view.units.sum()))
    right.metric('Observed sales value (USD)', '$' + compact(view.sales_value.sum()))
    st.caption('Selling-price value is neither profit nor inventory acquisition cost.')
    weekly = view.set_index('date').resample('W').units.sum().rename('Units').reset_index()
    st.altair_chart(alt.Chart(weekly).mark_line(color='#0F766E', strokeWidth=2).encode(
        x=alt.X('date:T', title=None, axis=alt.Axis(format='%b %Y', tickCount=6)), y=alt.Y('Units:Q', title='Weekly fulfilled units'),
        tooltip=[alt.Tooltip('date:T'), alt.Tooltip('Units:Q', format=',.0f')]).properties(height=270), use_container_width=True)
    products = view.groupby('item_id').agg(Units=('units', 'sum'), Sales_value=('sales_value', 'sum'), Zero_sales_share=('units', lambda x: (x == 0).mean())).sort_values('Units', ascending=False)
    products['Zero sales (%)'] = products.pop('Zero_sales_share') * 100
    products = products.rename(columns={'Sales_value': 'Sales value (USD)'}).reset_index().rename(columns={'item_id': 'Product'})
    st.subheader('Product contribution')
    st.dataframe(products.round(2), hide_index=True, width='stretch')
    with st.expander('Long zero-sales runs'):
        zero = pd.DataFrame(json.loads((OUT / 'zero_sales_diagnostics.json').read_text()))
        zero = zero[zero.item_id.isin(items)].sort_values('longest_zero_run_days', ascending=False)
        st.dataframe(zero.rename(columns={'item_id': 'Product', 'longest_zero_run_days': 'Longest zero-sales run (days)'}), hide_index=True, width='stretch')
        st.caption('Zero-sales runs do not identify stockouts. Assortment, availability, and demand may all contribute.')

elif page == 'Forecasts':
    st.subheader('Forecast evidence')
    period = st.radio('Evaluation period', ['Validation', 'Final holdout'], horizontal=True, key='period')
    name = 'validation_forecasts.parquet' if period == 'Validation' else 'final_forecasts.parquet'
    predictions = data(name)
    predictions = predictions[predictions.item_id.isin(items)]
    scores = forecast_metrics(predictions)
    scores['Model'] = scores.model.map(MODEL_LABELS)
    scores['WAPE (%)'] = scores.wape * 100
    table = scores[['Model', 'mae', 'WAPE (%)', 'bias']].rename(columns={'mae': 'MAE (units)', 'bias': 'Bias (units)'})
    st.dataframe(table.round(3), hide_index=True, width='stretch')
    st.caption(f"{len(items)} selected product{'s' if len(items) != 1 else ''}. MAE and bias are units per product-day; WAPE weights absolute errors by observed volume. Positive bias indicates overprediction.")
    st.info('Calendar ridge was selected on full-cohort validation before the final evaluation. On the full cohort, the 28-day average performed better on the final period. Filtering products changes displayed scores, not the frozen model selection.')
    product = st.selectbox('Inspect a product', items, key='forecast_product')
    history = predictions[predictions.item_id == product]
    history = history.assign(Series=history.model.map(MODEL_LABELS)).rename(columns={'prediction': 'Units'})
    actual = history.drop_duplicates('day_number')[['day_number', 'actual']].rename(columns={'actual': 'Units'})
    actual['Series'] = 'Observed sales'
    plot = pd.concat([history[['day_number', 'Units', 'Series']], actual], ignore_index=True)
    dates = sales[['day_number', 'date']].drop_duplicates('day_number')
    plot = plot.merge(dates, on='day_number', validate='many_to_one')
    st.altair_chart(chart(plot, 'Units', 'Daily sales units', group='Series'), use_container_width=True)
    st.caption('All 28 days are predicted at each forecast origin. The final period is now inspected; it is not an untouched test for later changes.')

st.divider()
with st.expander('Data provenance and metric definitions'):
    st.write('Source: M5 retail sales, University of Nicosia’s Zenodo mirror. This case study covers active products in one store and department; it is not representative of all retail inventory.')
    profile = json.loads((OUT / 'profile.json').read_text())
    st.caption(profile['checks'])
    st.write('Unit fill rate = fulfilled units / requested proxy units. Average closing stock = daily cohort closing-stock totals averaged over the replay. Undefined fill rates and percentage changes are shown as N/A. Final on-order stock is reported separately.')
    st.markdown('[Methodology and source code](https://github.com/ds-pouya/inventory-replenishment-analytics)')
