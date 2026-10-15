# Data sources and acquisition

Status as of 2026-10-15: official endpoint returned HTTP 401. Pouya selected the
university mirror for local analysis; acquisition and checksum verification implemented.
See docs/STATUS.md for the latest completed run.

## Primary source

[M5 Forecasting — Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data).
Obtain files from the official competition after reviewing its rules. Kaggle login
and acceptance may be required. Do not place credentials in this repository.
The competition data is subject to its rules, not an assumed open-data license.
Do not redistribute raw files or real-data samples until permission is established.

Expected inputs in `data/raw/m5/`:

| File | Grain / role |
| --- | --- |
| `sales_train_evaluation.csv` | item-store row with daily sales columns through d_1941 |
| `calendar.csv` | day key to date, week, events and state SNAP flags |
| `sell_prices.csv` | item-store-week selling price |

The sales hierarchy spans 3,049 products across 10 stores, forming 30,490 series.
Full evaluation sales reshape to about 59 million daily observations. These are
source descriptions; downloaded schemas and counts still require verification.

## Initial working slice

Start with store CA_1 and department FOODS_3. After profiling, select the 50 item IDs
with greatest observed unit sales in d_1 through d_1801, ties broken by item ID.
Freeze the list before comparing models. This targets active items, so conclusions
must not be generalized to slow-moving products or the full M5 hierarchy.

Use d_1..d_1801 for initial fitting/selection, four expanding 28-day validation
windows through d_1913, and d_1914..d_1941 as the final holdout. Preserve earlier
history for features. Future realized prices must not enter forecasts unless they
are explicitly treated as known-in-advance scenarios; event calendars may be known.

## Acquisition and profiling checklist

1. Download the three official files; preserve original filenames and bytes.
2. Save a local manifest: URL, retrieval time, byte count, SHA-256, accepted terms,
   source filename and coverage. Keep the manifest alongside ignored raw files.
3. Check required columns, numeric ranges, row keys and expected day coverage.
4. Check calendar day uniqueness and item-store-week price uniqueness.
5. Count missing prices and unmatched joins; define handling before reporting.
6. Export a small aggregate profile without redistributing source observations.

## Limitations

Sales are fulfilled transactions, not necessarily true demand. Stock availability,
lead times, orders, unit purchase costs and actual inventory are unavailable. Prices
are selling prices, not inventory acquisition costs. Do not convert zero-sales days
to observed stockouts. Scenario inputs must have their own provenance and labels.

No mirror is an automatic substitute for the original terms. If official access
fails, document it and evaluate a replacement before changing the project dataset.

## Approved local mirror

[University of Nicosia M5 record on Zenodo](https://zenodo.org/records/10203108),
DOI 10.5281/zenodo.10203108, links back to the official competition. Its API
metadata identifies access as open but does not specify a license. This does
not establish unrestricted redistribution rights. The user approved local use
on 2026-10-15. Raw data stays out of Git and no raw-data sample is published.

`scripts/download_data.py` fetches exactly the three listed files, verifies
provider MD5/size and records SHA-256, URLs, time and source metadata locally.
This mirror is recorded explicitly rather than passed off as a Kaggle download.
