"""Regenerate the distributable synthetic dashboard bundle."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.demo import build_demo

if __name__ == '__main__':
    print(json.dumps(build_demo(ROOT), indent=2))
