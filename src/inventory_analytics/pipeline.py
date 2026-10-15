"""Reproducible M5 loading, validation and training-only item selection."""
from pathlib import Path
import csv
import hashlib
import json
import tomllib
from datetime import datetime, timezone
import duckdb


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"filename": path.name, "bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(root):
    root = Path(root)
    cfg = tomllib.loads((root / "config/project.toml").read_text())
    raw = root / cfg["data"]["raw_directory"]
    paths = {k: raw / cfg["data"][k + "_file"] for k in ("sales", "calendar", "prices")}
    for path in paths.values():
        require(path.exists(), f"Missing source file: {path}. Run scripts/download_data.py first.")
    selection = cfg["subset"]
    cutoff = selection["selection_end_day"]
    end = cfg["evaluation"]["final_holdout_end_day"]
    with paths["sales"].open() as stream:
        columns = next(csv.reader(stream))
    day_cols = [f"d_{i}" for i in range(1, end + 1)]
    require(set(day_cols + ["item_id", "store_id", "dept_id", "state_id"]).issubset(columns),
            "Sales schema is missing required identifiers or day columns")
    con = duckdb.connect()
    con.execute("SET max_expression_depth TO 10000")
    try:
        for name, path in paths.items():
            if name == "sales":
                con.execute("CREATE TABLE sales AS SELECT * FROM read_csv_auto(?, sample_size=-1, types=?)",
                            [str(path), {day: "DOUBLE" for day in day_cols}])
            else:
                con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto(?, sample_size=-1)", [str(path)])
        one = lambda q: con.execute(q).fetchone()[0]
        for table, keys in [("sales", "item_id, store_id"), ("calendar", "d"),
                            ("prices", "item_id, store_id, wm_yr_wk")]:
            require(one(f"SELECT count(*) FROM (SELECT {keys}, count(*) n FROM {table} GROUP BY {keys} HAVING n > 1)") == 0,
                    f"Duplicate keys in {table}")
            nulls = ' OR '.join(f'{key.strip()} IS NULL' for key in keys.split(','))
            require(one(f"SELECT count(*) FROM {table} WHERE {nulls}") == 0, f"Null keys in {table}")
        require(one("SELECT count(*) FROM prices WHERE sell_price IS NULL OR sell_price <= 0") == 0,
                "Prices must be positive and non-null")
        train_sum = ' + '.join(f'coalesce(d_{i}, 0)' for i in range(1, cutoff + 1))
        con.execute(f"""CREATE TABLE selected AS SELECT *, ({train_sum}) AS selection_units
          FROM sales WHERE store_id = ? AND dept_id = ?
          ORDER BY selection_units DESC, item_id LIMIT ?""",
          [selection["store_id"], selection["dept_id"], selection["max_items"]])
        require(one("SELECT count(*) FROM selected") > 0, "Configured subset contains no items")
        con.execute(f"""CREATE TABLE daily AS
            UNPIVOT selected ON {', '.join(day_cols)} INTO NAME d VALUE units""")
        require(one("SELECT count(*) FROM daily") == one("SELECT count(*) FROM selected") * end,
                "Missing sales observations (null sales are not allowed)")
        require(one("SELECT count(*) FROM daily WHERE units < 0 OR units != floor(units)") == 0,
                "Sales units must be nonnegative integers")
        # Project the grain before joining: the UNPIVOT retains hierarchy columns.
        con.execute("""CREATE TABLE mart AS SELECT s.item_id, s.store_id, s.dept_id,
            s.state_id, s.d, CAST(substr(s.d, 3) AS INTEGER) AS day_number,
            CAST(c.date AS DATE) AS date, c.wm_yr_wk, s.units,
            p.sell_price, s.units * p.sell_price AS sales_value
            FROM daily s LEFT JOIN calendar c ON s.d = c.d
            LEFT JOIN prices p ON s.item_id = p.item_id AND s.store_id = p.store_id
            AND c.wm_yr_wk = p.wm_yr_wk""")
        require(one("SELECT count(*) FROM mart WHERE date IS NULL") == 0, "Missing calendar matches")
        require(one("SELECT count(*) FROM mart") == one("SELECT count(*) FROM daily"), "Join multiplied rows")
        require(one("SELECT sum(units) FROM mart") == one("SELECT sum(units) FROM daily"), "Units do not reconcile")
        require(one("SELECT count(*) FROM mart WHERE units > 0 AND sell_price IS NULL") == 0,
                "Positive sales have missing prices; investigate before calculating sales value")
        require(one("SELECT count(*) FROM (SELECT date FROM calendar GROUP BY date HAVING count(*) > 1)") == 0,
                "Calendar dates must be unique")
        out = root / "data/processed"
        out.mkdir(parents=True, exist_ok=True)
        # Publish mart only after all checks succeed.
        temp = out / "daily_sales.tmp.parquet"
        con.execute("COPY (SELECT * FROM mart ORDER BY item_id, day_number) TO ? (FORMAT PARQUET)", [str(temp)])
        temp.replace(out / "daily_sales.parquet")
        profile = {
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "inputs": [fingerprint(path) for path in paths.values()],
            "source_rows": {name: one(f"SELECT count(*) FROM {name}") for name in paths},
            "subset": selection,
            "selected_items": [r[0] for r in con.execute("SELECT item_id FROM selected ORDER BY item_id").fetchall()],
            "daily_rows": one("SELECT count(*) FROM mart"),
            "total_units": one("SELECT sum(units) FROM mart"),
            "unpriced_zero_sales_rows": one("SELECT count(*) FROM mart WHERE sell_price IS NULL"),
            "date_min": str(one("SELECT min(date) FROM mart")),
            "date_max": str(one("SELECT max(date) FROM mart")),
            "checks": "passed: keys, sales ranges, calendar matches, join cardinality, units and positive-sales price coverage",
        }
        (out / "profile.json").write_text(json.dumps(profile, indent=2))
        (out / "build_config.json").write_text(json.dumps(cfg, indent=2))
        return profile
    finally:
        con.close()
