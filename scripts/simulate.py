"""Replay inventory policies using the frozen forecast and scenario specification."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.simulation import run
if __name__ == '__main__':
    result = run(ROOT)
    print(json.dumps([row for row in result['results'] if row['is_base_case']], indent=2))
