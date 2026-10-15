import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.forecasting import backtest, evaluate, forecast_at_origin, score, zero_run_profile
import tomllib
SPEC = tomllib.loads((ROOT / 'config/forecasting.toml').read_text())


class ForecastingTest(unittest.TestCase):
    def fixture(self, root):
        out = root / 'data/processed'
        out.mkdir(parents=True)
        raw = root / 'data/raw/m5'
        raw.mkdir(parents=True)
        (root / 'config').mkdir()
        (root / 'docs').mkdir()
        shutil.copy(ROOT / 'config/forecasting.toml', root / 'config/forecasting.toml')
        cfg = {'evaluation': {'horizon_days': 7, 'initial_train_end_day': 28,
                'validation_windows': 2, 'final_holdout_start_day': 43, 'final_holdout_end_day': 49},
               'data': {'raw_directory': 'data/raw/m5', 'calendar_file': 'calendar.csv'}}
        (out / 'build_config.json').write_text(json.dumps(cfg))
        frame = pd.DataFrame({'item_id': ['A'] * 49, 'day_number': range(1, 50),
            'units': [i % 7 for i in range(1, 50)], 'd': [f'd_{i}' for i in range(1, 50)],
            'state_id': ['CA'] * 49, 'date': pd.date_range('2020-01-01', periods=49)})
        frame.to_parquet(out / 'daily_sales.parquet')
        pd.DataFrame({'d': frame.d, 'event_name_1': [None] * 49, 'event_name_2': [None] * 49,
            'snap_CA': [0] * 49, 'snap_TX': [0] * 49, 'snap_WI': [0] * 49}).to_csv(raw / 'calendar.csv', index=False)
        return out, frame

    def test_final_outcomes_do_not_affect_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out, frame = self.fixture(root)
            original = backtest(root)
            self.assertTrue(all(s['mae'] == 0 for s in original if s['model'] == 'seasonal_naive_7'))
            frame.loc[frame.day_number >= 43, 'units'] = 9999
            frame.to_parquet(out / 'daily_sales.parquet')
            self.assertEqual(backtest(root), original)
            self.assertLess(pd.read_parquet(out / 'validation_forecasts.parquet').day_number.max(), 43)

    def test_all_predictions_ignore_sales_inside_forecast_horizon(self):
        frame = pd.DataFrame({'date': pd.date_range('2020-01-01', periods=70),
            'day_number': range(1, 71), 'units': [i % 7 + 2 for i in range(70)], 'snap': 0, 'event': 0})
        _, original = forecast_at_origin(frame, 42, 28, SPEC)
        frame.loc[frame.day_number > 42, 'units'] = 99999
        _, changed = forecast_at_origin(frame, 42, 28, SPEC)
        for model in original:
            np.testing.assert_array_equal(original[model], changed[model])
            self.assertTrue(np.isfinite(changed[model]).all())
            self.assertTrue((changed[model] >= 0).all())

    def test_calendar_model_learns_weekday_pattern(self):
        days = np.arange(1, 401)
        frame = pd.DataFrame({'date': pd.date_range('2020-01-01', periods=400),
            'day_number': days, 'units': np.where(days % 7 == 0, 30., 2.), 'snap': 0, 'event': 0})
        future, forecasts = forecast_at_origin(frame, 364, 28, SPEC)
        self.assertLess(np.abs(future.units - forecasts['calendar_ridge']).mean(),
                        np.abs(future.units - forecasts['mean_28']).mean())

    def test_zero_demand_has_undefined_wape(self):
        frame = pd.DataFrame({'origin': [28], 'model': ['test'], 'actual': [0.], 'prediction': [0.]})
        self.assertIsNone(score(frame)[0]['wape'])
        self.assertEqual(score(frame)[0]['mae'], 0)

    def test_zero_runs_use_training_only(self):
        frame = pd.DataFrame({'item_id': ['A'] * 40, 'day_number': range(1, 41), 'units': [0] * 30 + [1] * 10})
        result = zero_run_profile(frame, 28)[0]
        self.assertEqual(result['longest_zero_run_days'], 28)
        self.assertEqual(result['zero_runs_at_least_28_days'], 1)
        self.assertEqual(result['leading_zero_days'], 28)
        self.assertEqual(result['trailing_zero_days'], 28)

    def test_frozen_evaluation_and_changed_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out, frame = self.fixture(root)
            backtest(root)
            shutil.copy(out / 'forecast_selection.json', root / 'docs/FORECAST_SELECTION.json')
            result = evaluate(root)
            self.assertEqual(result['selected_model'], 'seasonal_naive_7')
            final = pd.read_parquet(out / 'final_forecasts.parquet')
            self.assertEqual((final.day_number.min(), final.day_number.max()), (43, 49))
            frame.loc[frame.day_number == 49, 'units'] = 17
            frame.to_parquet(out / 'daily_sales.parquet')
            with self.assertRaisesRegex(ValueError, 'differs from the frozen selection'):
                evaluate(root)
