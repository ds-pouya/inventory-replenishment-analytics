"""Create a deterministic public example without reading the M5 source data."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np
import pandas as pd

from inventory_analytics.pipeline import build as build_mart
from inventory_analytics.forecasting import backtest, evaluate
from inventory_analytics.simulation import run as simulate

SEED = 20261019
ITEMS = 24
DAYS = 1941
FILES = ('daily_sales.parquet', 'profile.json', 'build_config.json',
         'simulation_summary.json', 'simulation_daily.parquet',
         'validation_forecasts.parquet', 'final_forecasts.parquet',
         'zero_sales_diagnostics.json')


def generate_source(root):
    """Use declared distributions, never parameters estimated from retailer data."""
    raw = root / 'data/raw/synthetic'
    raw.mkdir(parents=True)
    rng = np.random.default_rng(SEED)
    dates = pd.date_range('2021-01-04', periods=DAYS + 28)
    day = np.arange(1, len(dates) + 1)
    calendar = pd.DataFrame({'date': dates.strftime('%Y-%m-%d'), 'd': ['d_' + str(n) for n in day],
        'wm_yr_wk': (day - 1) // 7 + 1,
        'event_name_1': np.where((day % 45) == 0, 'Demo promotion', None),
        'event_name_2': [None] * len(day),
        'snap_CA': (dates.day <= 10).astype(int), 'snap_TX': 0, 'snap_WI': 0})
    calendar.to_csv(raw / 'calendar.csv', index=False)
    sales, prices = [], []
    for i in range(ITEMS):
        item = f'DEMO_{i+1:03d}'
        base = float(rng.uniform(4, 28))
        weekend = 1 + rng.uniform(.1, .55) * (dates.dayofweek >= 5)
        annual = 1 + .22 * np.sin(2 * np.pi * day / 365.25 + i / 3)
        growth = 1 + rng.uniform(-.15, .25) * day / DAYS
        promotion = 1 + .4 * ((day % 45) == 0)
        units = rng.poisson(np.maximum(.1, base * weekend * annual * growth * promotion))
        if i % 6 == 0:
            units[rng.random(len(day)) < .3] = 0  # Synthetic intermittency.
        if i % 8 == 0:
            units[500:540] = 0  # Synthetic zero-sales run, no stockout claim.
        sales.append({'item_id': item, 'store_id': 'DEMO_STORE', 'dept_id': 'DEMO_PRODUCTS',
                      'state_id': 'CA', **{f'd_{n}': int(units[n-1]) for n in range(1, DAYS+1)}})
        price = round(float(rng.uniform(1.5, 8)), 2)
        prices.extend({'item_id': item, 'store_id': 'DEMO_STORE', 'wm_yr_wk': int(week),
                       'sell_price': price} for week in calendar.wm_yr_wk.unique())
    pd.DataFrame(sales).to_csv(raw / 'sales.csv', index=False)
    pd.DataFrame(prices).to_csv(raw / 'prices.csv', index=False)
    return raw


def build_demo(project_root, destination=None):
    project_root = Path(project_root)
    destination = Path(destination) if destination else project_root / 'data/demo'
    # The disposable root keeps synthetic selection and outputs separate from M5.
    with tempfile.TemporaryDirectory(prefix='inventory-demo-') as temporary:
        root = Path(temporary)
        (root / 'config').mkdir()
        (root / 'docs').mkdir()
        for name in ('forecasting.toml', 'scenarios.toml'):
            shutil.copyfile(project_root / 'config' / name, root / 'config' / name)
        (root / 'config/project.toml').write_text(f'''[data]
source = "independent-synthetic-example"
raw_directory = "data/raw/synthetic"
sales_file = "sales.csv"
calendar_file = "calendar.csv"
prices_file = "prices.csv"
[subset]
store_id = "DEMO_STORE"
dept_id = "DEMO_PRODUCTS"
max_items = {ITEMS}
selection_end_day = 1801
selection_rule = "all generated products"
[evaluation]
initial_train_end_day = 1801
validation_windows = 4
horizon_days = 28
final_holdout_start_day = 1914
final_holdout_end_day = 1941
''')
        generate_source(root)
        build_mart(root)
        backtest(root)
        out = root / 'data/processed'
        # Demonstrate validation-first selection inside this synthetic run.
        shutil.copyfile(out / 'forecast_selection.json', root / 'docs/FORECAST_SELECTION.json')
        evaluate(root)
        simulate(root)
        profile = json.loads((out / 'profile.json').read_text())
        profile.pop('built_at_utc')  # Stable public output, no run-specific timestamp.
        (out / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
        manifest = {'kind': 'synthetic', 'seed': SEED, 'products': ITEMS,
            'description': 'Independently generated example; no M5 records or fitted M5 parameters. Metrics do not represent the M5 case study.',
            'generator': 'src/inventory_analytics/demo.py',
            'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'numpy_version': np.__version__, 'files': {}}
        destination.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            shutil.copyfile(out / name, destination / name)
            path = destination / name
            manifest['files'][name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
        (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        return manifest
