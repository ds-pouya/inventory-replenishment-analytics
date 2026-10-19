"""Build local reporting extracts and the native report source package."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inventory_analytics.native_reporting import build

if __name__ == '__main__':
    print(json.dumps(build(ROOT), indent=2))
