"""Synthetic fixtures test selection leakage and financial join failures."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inventory_analytics.pipeline import build


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        self.raw = self.root / 'data/raw/m5'
        self.raw.mkdir(parents=True)
        (self.root / 'config/project.toml').write_text('''[data]
raw_directory = "data/raw/m5"
sales_file = "sales.csv"
calendar_file = "calendar.csv"
prices_file = "prices.csv"
[subset]
store_id = "CA_1"
dept_id = "FOODS_3"
max_items = 1
selection_end_day = 2
[evaluation]
final_holdout_end_day = 4
''')
        self.write('sales.csv', ['item_id','store_id','dept_id','state_id','d_1','d_2','d_3','d_4'],
                   [['A','CA_1','FOODS_3','CA',5,5,1,1], ['B','CA_1','FOODS_3','CA',1,1,999,999]])
        self.write('calendar.csv', ['d','date','wm_yr_wk'], [[f'd_{i}',f'2020-01-0{i}',1] for i in range(1,5)])
        self.write('prices.csv', ['item_id','store_id','wm_yr_wk','sell_price'], [['A','CA_1',1,2],['B','CA_1',1,3]])

    def write(self, name, header, rows):
        with (self.raw/name).open('w', newline='') as stream:
            writer=csv.writer(stream); writer.writerow(header); writer.writerows(rows)

    def test_future_sales_do_not_change_selection_and_rerun_matches(self):
        profile=build(self.root)
        self.assertEqual(profile['selected_items'], ['A'])
        self.assertEqual(profile['daily_rows'], 4)
        self.assertEqual(profile['total_units'], 12)
        self.assertEqual(build(self.root)['total_units'], 12)

    def test_duplicate_prices_rejected_before_output(self):
        with (self.raw/'prices.csv').open('a', newline='') as stream:
            csv.writer(stream).writerow(['A','CA_1',1,4])
        with self.assertRaisesRegex(ValueError, 'Duplicate keys in prices'):
            build(self.root)
        self.assertFalse((self.root/'data/processed/daily_sales.parquet').exists())

    def test_missing_price_for_positive_sales_rejected(self):
        self.write('prices.csv', ['item_id','store_id','wm_yr_wk','sell_price'], [['B','CA_1',1,3]])
        with self.assertRaisesRegex(ValueError, 'Positive sales have missing prices'):
            build(self.root)

    def test_missing_calendar_day_rejected(self):
        self.write('calendar.csv', ['d','date','wm_yr_wk'], [['d_1','2020-01-01',1]])
        with self.assertRaisesRegex(ValueError, 'Missing calendar matches'):
            build(self.root)

    def test_missing_sales_not_silently_dropped(self):
        self.write('sales.csv', ['item_id','store_id','dept_id','state_id','d_1','d_2','d_3','d_4'],
                   [['A','CA_1','FOODS_3','CA',5,5,'',1]])
        with self.assertRaisesRegex(ValueError, 'Missing sales observations'):
            build(self.root)

    def test_zero_sales_without_price_are_counted_not_imputed(self):
        self.write('sales.csv', ['item_id','store_id','dept_id','state_id','d_1','d_2','d_3','d_4'],
                   [['A','CA_1','FOODS_3','CA',0,0,0,0]])
        self.write('prices.csv', ['item_id','store_id','wm_yr_wk','sell_price'], [['B','CA_1',1,3]])
        profile = build(self.root)
        self.assertEqual(profile['unpriced_zero_sales_rows'], 4)
        self.assertEqual(profile['total_units'], 0)

if __name__ == '__main__':
    unittest.main()
