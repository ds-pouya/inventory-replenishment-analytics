"""Local integration checks; source data is not required for unit-test runs."""
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless((ROOT / 'data/processed/simulation_daily.parquet').exists(), 'Build local analysis before dashboard integration checks')
class DashboardTest(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(str(ROOT / 'app/streamlit_app.py')).run(timeout=30)
        self.assertFalse(app.exception)
        return app

    def test_base_tradeoff_and_all_views_render(self):
        app = self.app()
        self.assertEqual([m.value for m in app.metric], ['-17.7%', '-0.96 pp'])
        self.assertIn('Neither policy', app.subheader[0].value)
        for page in ['Inventory', 'Demand', 'Forecasts']:
            app.radio(key='page').set_value(page).run(timeout=30)
            self.assertFalse(app.exception, page)
        app.radio(key='period').set_value('Final holdout').run()
        self.assertFalse(app.exception)
        scores = app.dataframe[0].value.set_index('Model')
        self.assertAlmostEqual(scores.loc['28-day average', 'MAE (units)'], 5.911, places=3)

    def test_scenario_threshold_and_empty_selection(self):
        app = self.app()
        app.selectbox(key='lead').set_value(3).run()
        self.assertFalse(app.exception)
        self.assertIn('Order-up-to', app.subheader[0].value)
        app.slider(key='threshold').set_value(100.).run()
        self.assertIn('Neither policy', app.subheader[0].value)
        app.multiselect(key='products').set_value([]).run()
        self.assertTrue(app.warning)
        self.assertFalse(app.exception)

    def test_product_filter_changes_forecast_cohort(self):
        app = self.app()
        app.multiselect(key='products').set_value(['FOODS_3_030']).run()
        app.radio(key='page').set_value('Forecasts').run(timeout=30)
        self.assertFalse(app.exception)
        self.assertTrue(any('1 selected product' in caption.value for caption in app.caption))
        self.assertEqual(list(app.selectbox(key='forecast_product').options), ['FOODS_3_030'])
        # This product is zero throughout the first validation window; the pooled
        # score must differ from the full-cohort 6.101, not reuse a global summary.
        self.assertNotEqual(app.dataframe[0].value.iloc[0]['MAE (units)'], 6.101)
