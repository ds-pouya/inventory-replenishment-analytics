"""Public demo checks that run without private or downloaded retail inputs."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.demo import FILES, ITEMS, generate_source


class DemoTest(unittest.TestCase):
    def test_bundle_integrity_and_synthetic_grain(self):
        folder = ROOT / 'data/demo'
        manifest = json.loads((folder / 'manifest.json').read_text())
        self.assertEqual(manifest['kind'], 'synthetic')
        self.assertEqual(set(manifest['files']), set(FILES))
        for name, record in manifest['files'].items():
            self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), record['sha256'])
        sales = pd.read_parquet(folder / 'daily_sales.parquet')
        self.assertEqual(sales.item_id.nunique(), ITEMS)
        self.assertTrue(sales.item_id.str.startswith('DEMO_').all())
        self.assertEqual(set(sales.store_id), {'DEMO_STORE'})
        self.assertFalse(sales.duplicated(['item_id', 'day_number']).any())
        ledger = pd.read_parquet(folder / 'simulation_daily.parquet')
        self.assertEqual(len(ledger), ITEMS * 28 * 9 * 2)
        self.assertTrue((ledger.fulfilled_units + ledger.lost_units == ledger.demand_proxy_units).all())
        summary = json.loads((folder / 'simulation_summary.json').read_text())
        for row in summary['results']:
            group = ledger[(ledger.scenario_id == row['scenario_id']) & (ledger.policy == row['policy'])]
            self.assertAlmostEqual(group.fulfilled_units.sum() / group.demand_proxy_units.sum(), row['unit_fill_rate'])
            self.assertAlmostEqual(group.groupby('date').ending_stock.sum().mean(), row['average_ending_inventory'])

    def test_source_generation_is_repeatable_and_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / 'a', Path(directory) / 'b'
            a, b = generate_source(first), generate_source(second)
            for name in ('sales.csv', 'calendar.csv', 'prices.csv'):
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())
            self.assertFalse((first / 'data/raw/m5').exists())

    def test_public_entry_runs_from_clean_checkout_without_m5(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('app', 'src', 'data/demo'):
                shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns('__pycache__'))
            app = AppTest.from_file(str(root / 'app/demo_app.py')).run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(any('SYNTHETIC DEMO' in info.value for info in app.info))
            self.assertEqual(len(app.multiselect(key='products').options), ITEMS)
            for page in ('Inventory', 'Demand', 'Forecasts'):
                app.radio(key='page').set_value(page).run(timeout=30)
                self.assertFalse(app.exception, page)
                self.assertTrue(any('SYNTHETIC DEMO' in info.value for info in app.info))
            app.radio(key='period').set_value('Final holdout').run()
            app.multiselect(key='products').set_value(['DEMO_001']).run()
            self.assertFalse(app.exception)
            self.assertEqual(list(app.selectbox(key='forecast_product').options), ['DEMO_001'])
            app.radio(key='page').set_value('Overview').run()
            app.selectbox(key='lead').set_value(14).run()
            app.selectbox(key='cover').set_value(7).run()
            app.slider(key='threshold').set_value(100.).run()
            self.assertFalse(app.exception)
            app.multiselect(key='products').set_value([]).run()
            self.assertTrue(app.warning)
            self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()
