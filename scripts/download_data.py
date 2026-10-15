"""Acquire university mirror files; verify provider MD5 and record SHA-256."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from inventory_analytics.pipeline import fingerprint
RECORD = "https://zenodo.org/api/records/10203108"
FILES = ("calendar.csv", "sales_train_evaluation.csv", "sell_prices.csv")


def md5(path):
    digest = hashlib.md5()  # Provider integrity checksum, not a security primitive.
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    raw = ROOT / "data/raw/m5"
    raw.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(RECORD, timeout=60) as response:
        metadata = json.load(response)
    manifest = {"record": RECORD, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "usage": "Local analysis via university mirror; no license specified in record metadata; raw data excluded from Git.",
                "files": []}
    entries = {entry["key"]: entry for entry in metadata["files"]}
    for name in FILES:
        entry = entries[name]
        target = raw / name
        expected = entry["checksum"].removeprefix("md5:")
        if not target.exists():
            print(f"Downloading {name} ({entry['size']:,} bytes)", flush=True)
            partial = target.with_suffix(".csv.part")
            with urllib.request.urlopen(entry["links"]["self"], timeout=120) as response, partial.open("wb") as output:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    output.write(block)
            if partial.stat().st_size != entry["size"] or md5(partial) != expected:
                raise ValueError(f"Integrity check failed: {name}; partial retained for inspection")
            partial.replace(target)
        if target.stat().st_size != entry["size"] or md5(target) != expected:
            raise ValueError(f"Existing file differs from source: {name}; refusing overwrite")
        manifest["files"].append({**fingerprint(target), "url": entry["links"]["self"], "provider_md5": expected})
        (raw / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"Verified {name}", flush=True)
    (raw / "record_metadata.json").write_text(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
