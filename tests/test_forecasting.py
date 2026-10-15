import json
from pathlib import Path
import sys
import tempfile
import unittest
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inventory_analytics.forecasting import backtest

class ForecastingTest(unittest.TestCase):
    def test_weekly_pattern_and_future_independence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); out=root/'data/processed'; out.mkdir(parents=True)
            cfg={'evaluation':{'horizon_days':7,'initial_train_end_day':28,
                'validation_windows':2,'final_holdout_start_day':43}}
            (out/'build_config.json').write_text(json.dumps(cfg))
            frame=pd.DataFrame({'item_id':['A']*49,'day_number':range(1,50),
                                'units':[i%7 for i in range(1,50)]})
            frame.to_parquet(out/'daily_sales.parquet')
            original=backtest(root)
            self.assertTrue(all(s['mae']==0 for s in original if s['model']=='seasonal_naive_7'))
            frame.loc[frame.day_number>=43,'units']=9999
            frame.to_parquet(out/'daily_sales.parquet')
            self.assertEqual(backtest(root),original)
            forecasts=pd.read_parquet(out/'validation_forecasts.parquet')
            self.assertLess(forecasts.day_number.max(),43)
