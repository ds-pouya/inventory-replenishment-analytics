"""Run from any working directory: python scripts/build_data.py."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from inventory_analytics.pipeline import build
if __name__ == "__main__":
    print(json.dumps(build(ROOT), indent=2))
