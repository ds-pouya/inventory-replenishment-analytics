# Data sources and acquisition

The project uses M5 retail sales data from the
[University of Nicosia record on Zenodo](https://zenodo.org/records/10203108),
DOI 10.5281/zenodo.10203108. The record links to the original
[M5 Forecasting — Accuracy competition](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data).

The initial download and profiling were completed on 2026-10-15. The university
mirror provides reproducible file access without Kaggle authentication. Source
metadata and file fingerprints accompany the local inputs.

## Source tables

| File | Grain / role | Verified rows |
| --- | --- | ---: |
| `sales_train_evaluation.csv` | item-store row with daily sales through d_1941 | 30,490 |
| `calendar.csv` | day key, date, week, events and state SNAP flags | 1,969 |
| `sell_prices.csv` | item-store-week selling price | 6,841,121 |

The sales hierarchy contains 3,049 products across 10 stores. Reshaping all
1,941 observed days would produce approximately 59 million item-day records.

## Working subset

The first mart contains the 50 products with the highest unit sales at store CA_1,
department FOODS_3, during d_1 through d_1801. Item ID breaks ties. The resulting
97,050 observations span 2011-01-29 through 2016-05-22.

Selection uses only the initial training interval. This favors active products,
so results do not represent slow-moving products or the full M5 hierarchy.

The evaluation schedule uses d_1..d_1801 for initial fitting and selection, four
expanding 28-day validation windows through d_1913, and d_1914..d_1941 as the final
holdout. Future realized selling prices are excluded from the baseline forecasts.
Calendar events may support later models when known at forecast time.

## Acquisition and validation

`scripts/download_data.py` retrieves the three CSV files into `data/raw/m5/`.
It verifies provider MD5 checksums and file sizes, then records SHA-256 hashes,
source URLs, retrieval time, and the source metadata. Interrupted downloads retain
a `.part` file and restart on the next run. Mismatched existing files cause an error.

`scripts/build_data.py` checks required sales columns, table keys, sales ranges,
calendar matches, price coverage, join cardinality, and unit reconciliation. The
build profile reports 6,111 zero-sales records without prices in the working subset.
No positive-sales record is missing a price.

## Reuse and attribution

The Zenodo API identifies access as open but does not specify a license. The
original competition has its own rules. Public access does not establish
unrestricted redistribution rights. Raw data, real-data samples, generated marts,
and local manifests are excluded from Git. The repository contains code,
documentation, synthetic test fixtures, and aggregate evaluation results.

## Analytical limitations

Sales record fulfilled transactions rather than unconstrained demand. Stock
availability, supplier lead times, orders, acquisition costs, and actual inventory
are absent. Zero sales do not establish a stockout, and selling prices do not
establish profit. Inventory policy comparisons will therefore use documented
scenario assumptions and report simulated outcomes separately from observed sales.
