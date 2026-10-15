"""Hand-calculated inventory scenarios and accounting edge cases."""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inventory_analytics.simulation import aggregate, simulate, summarize


class SimulationTest(unittest.TestCase):
    def test_receipt_timing_and_lost_sales(self):
        ledger = simulate([5, 5, 5, 5], 5, 2, 1, 'fixed_cover', 5)
        self.assertEqual(ledger.receipts.tolist(), [0, 0, 5, 5])
        self.assertEqual(ledger.fulfilled_units.tolist(), [5, 0, 5, 5])
        self.assertEqual(ledger.lost_units.tolist(), [0, 5, 0, 0])
        result = summarize(ledger)
        self.assertEqual(result['unit_fill_rate'], .75)
        self.assertEqual(result['ending_on_order'], 10)
        self.assertEqual(result['ending_stock'], 0)

    def test_orders_in_transit_prevent_duplicate_replenishment(self):
        ledger = simulate([0, 0, 0, 0], 0, 3, 1, 'order_up_to', targets=[10] * 4)
        self.assertEqual(ledger.ordered_units.tolist(), [10, 0, 0, 0])
        self.assertEqual(ledger.receipts.tolist(), [0, 0, 0, 10])
        self.assertEqual(ledger.ending_stock.iloc[-1], 10)

    def test_review_cadence_and_one_day_lead(self):
        ledger = simulate([0] * 5, 0, 1, 2, 'fixed_cover', 3)
        self.assertEqual(ledger.ordered_units.tolist(), [3, 0, 3, 0, 3])
        self.assertEqual(ledger.receipts.tolist(), [0, 3, 0, 3, 0])
        self.assertEqual(ledger.ending_on_order.iloc[-1], 3)

    def test_target_rounding_and_initial_inventory_position(self):
        ledger = simulate([1], 4, 1, 1, 'order_up_to', targets=[10.2])
        self.assertEqual(ledger.ordered_units.iloc[0], 7)
        self.assertEqual(ledger.ending_stock.iloc[0], 3)
        self.assertEqual(ledger.inventory_position_before_order.iloc[0], 4)

    def test_zero_demand_fill_rate_is_undefined(self):
        self.assertIsNone(summarize(simulate([0] * 3, 0, 1, 1, 'fixed_cover', 0))['unit_fill_rate'])

    def test_no_negative_orders_when_overstocked(self):
        ledger = simulate([1, 1, 1], 100, 2, 1, 'order_up_to', targets=[5] * 3)
        self.assertEqual(ledger.ordered_units.sum(), 0)
        self.assertEqual(ledger.ending_stock.iloc[-1], 97)

    def test_invalid_inputs_rejected(self):
        for demand in ([1.5], [-1], [np.nan], [], [np.inf]):
            with self.subTest(demand=demand), self.assertRaises(ValueError):
                simulate(demand, 0, 1, 1, 'fixed_cover')
        for lead in (0, -1, 1.5, True):
            with self.subTest(lead=lead), self.assertRaises(ValueError):
                simulate([1], 0, lead, 1, 'fixed_cover')
        with self.assertRaises(ValueError):
            simulate([1], 0, 1, 1, 'order_up_to', targets=[np.nan])

    def test_cohort_metrics_weight_units_and_sum_inventory(self):
        a = simulate([10, 10], 10, 3, 1, 'fixed_cover', 0)
        b = simulate([1, 1], 10, 3, 1, 'fixed_cover', 0)
        result = aggregate(pd.concat([a, b], ignore_index=True))
        self.assertAlmostEqual(result['unit_fill_rate'], 12 / 22)
        self.assertEqual(result['average_ending_inventory'], 8.5)
        self.assertEqual(result['ending_stock'], 8)

    def test_future_demand_cannot_change_earlier_orders(self):
        first = simulate([2, 2, 2, 2], 8, 2, 1, 'order_up_to', targets=[10] * 4)
        changed = simulate([2, 2, 200, 200], 8, 2, 1, 'order_up_to', targets=[10] * 4)
        pd.testing.assert_frame_equal(first.iloc[:2], changed.iloc[:2])
