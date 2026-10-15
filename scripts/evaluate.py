"""Score the final holdout using the previously frozen model-selection record."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.forecasting import evaluate
if __name__ == '__main__':
    print(json.dumps(evaluate(ROOT), indent=2))
