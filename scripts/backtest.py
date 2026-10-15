"""Compare simple baselines on validation windows, never the final holdout."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from inventory_analytics.forecasting import backtest
if __name__=='__main__':
    print(json.dumps(backtest(ROOT),indent=2))
