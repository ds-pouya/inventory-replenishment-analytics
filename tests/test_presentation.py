"""Decision summaries must respect service constraints and undefined metrics."""
from pathlib import Path
import sys
import unittest
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inventory_analytics.presentation import decision_summary, forecast_metrics


def pair(fixed_fill=.9483, order_fill=.9388, fixed_stock=100, order_stock=80):
    return pd.DataFrame({'policy': ['fixed_cover', 'order_up_to'],
        'unit_fill_rate': [fixed_fill, order_fill],
        'average_ending_inventory': [fixed_stock, order_stock]})


class PresentationTest(unittest.TestCase):
    def test_lower_stock_is_not_recommended_when_both_miss_threshold(self):
        result = decision_summary(pair(), .95)
        self.assertIsNone(result['winner'])
        self.assertIn('Neither', result['title'])
        self.assertAlmostEqual(result['stock_change_pct'], -20)
        self.assertAlmostEqual(result['fill_change_pp'], -.95)

    def test_service_constraint_takes_precedence_over_less_stock(self):
        result = decision_summary(pair(.96, .94), .95)
        self.assertEqual(result['winner'], 'fixed_cover')

    def test_lowest_stock_qualifying_policy_is_selected(self):
        result = decision_summary(pair(.96, .95), .95)
        self.assertEqual(result['winner'], 'order_up_to')

    def test_undefined_service_and_zero_stock_do_not_create_recommendation(self):
        result = decision_summary(pair(None, None, 0, 0), .95)
        self.assertIsNone(result['winner'])
        self.assertIsNone(result['stock_change_pct'])
        self.assertIsNone(result['fill_change_pp'])
        self.assertIn('No requested units', result['title'])

    def test_equal_stock_does_not_claim_a_reduction(self):
        result = decision_summary(pair(.97, .96, 100, 100), .95)
        self.assertIn('equal stock', result['title'])

    def test_invalid_threshold_rejected(self):
        for threshold in (-.1, 1.1, float('nan')):
            with self.assertRaises(ValueError):
                decision_summary(pair(), threshold)

    def test_forecast_scores_use_volume_weighting_and_handle_zero_actuals(self):
        frame = pd.DataFrame({'model': ['a', 'a'], 'actual': [10., 1.], 'prediction': [8., 0.]})
        row = forecast_metrics(frame).iloc[0]
        self.assertAlmostEqual(row.mae, 1.5)
        self.assertAlmostEqual(row.wape, 3 / 11)
        self.assertAlmostEqual(row.bias, -1.5)
        frame['actual'] = 0
        self.assertIsNone(forecast_metrics(frame).iloc[0].wape)
