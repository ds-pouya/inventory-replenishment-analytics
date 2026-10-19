# Technical walkthrough

This walkthrough follows the path from source files to the inventory decision.
A full demonstration takes approximately six to eight minutes.

## 1. Start with the decision

The question is whether a lower-stock policy maintains an acceptable fulfillment
level under stated lead-time and starting-stock assumptions. The dashboard makes
the service preference visible rather than equating inventory reduction with savings.

The base case compares seven-day lead time, weekly reviews, and 14 days of initial
cover. Fixed cover reaches 94.83% simulated fill with 7,292.3 average closing units;
order-up-to reaches 93.88% with 5,998.1. Neither qualifies at the 95% planning
threshold. The inventory reduction is a tradeoff, not a demonstrated economic benefit.

## 2. Trace the source and grain

Three M5 files supply the analysis:

- Sales: one product-store row with daily sales columns.
- Calendar: a day key, date, week, events, and state SNAP flags.
- Prices: one product-store-week selling price.

`scripts/download_data.py` verifies the university mirror's published sizes and
MD5 checksums and records SHA-256 fingerprints, URLs, retrieval time, and metadata
with the local inputs. Source records remain outside version control.

`pipeline.py` reshapes sales into item-store-day observations. Calendar joins on
the day key; prices join on item, store, and week. Key uniqueness prevents joins
from multiplying sales. Counts and total units are reconciled after joining.
Missing prices are allowed only on zero-sales records and counted explicitly.

The full sales source would produce roughly 59 million daily observations. The
working slice contains 50 active products from one department/store. Selection
uses units sold through day 1801, with item ID breaking ties. This gives a
reproducible local workload but favors active products; it is not a retailer-wide sample.

## 3. Follow the chronology

The initial fitting/selection period ends at day 1801. Four expanding 28-day
validation windows cover days 1802–1913. The final period is days 1914–1941.
Each forecast predicts its full horizon using only observations at its origin.

The candidates are previous-week repetition, a recent 28-day mean, and calendar
ridge. The regression fits each product's most recent 364 days with weekday,
annual-cycle, trend, event, and SNAP features. Its ridge penalty is fixed at 10;
the intercept is unpenalized and predictions are clipped at zero.

Only calendar inputs known at forecast time enter future features. Future sales
and realized future prices are excluded. Tests change later outcomes and verify
that earlier predictions remain unchanged.

Pooled validation MAE selects calendar ridge. The selection record and hashes were
committed in `212c40a` before final scoring. `evaluate.py` rejects changed data,
configuration, or forecast implementation instead of silently evaluating a different model.
The final comparison is recorded in the following results commit, `77fbbce`.

Calendar ridge scores 6.060 final MAE, versus 5.911 for the recent mean. The selected
model remains fixed. The final period is now inspected, so later changes cannot
reuse it as an untouched test. A lower validation error did not ensure a lower final error.

## 4. Read an inventory ledger

`simulation.py` replays the observed final-period sales as requested units.
Both policies receive the same initial stock and demand proxy in each scenario.
Orders start with an empty pipeline; unmet units are lost rather than backordered.

The daily sequence is receipts, opening review/orders, demand fulfillment, then
closing stock. An order placed on day t arrives before demand on t + lead time.
Reviews happen on day 1 and every seven days afterward.

Fixed cover orders a constant review-period quantity based on the pre-start
28-day mean. Order-up-to subtracts on-hand plus incoming inventory from a target
covering lead time plus review time, with an approximate safety buffer.
Subtracting incoming orders prevents double replenishment.

Forecasts remain fixed at day 1913. Known calendar rows extend predictions beyond
the replay, so late reviews have a full protection interval. Safety variability
comes from the 112 earlier validation errors per product, not replay outcomes.

The buffer's nominal 95% parameter uses a normal quantile and square-root-of-time
scaling. Correlated, intermittent, or biased errors can violate those assumptions;
it is not a promise of 95% unit fill. No monetary objective or fitted bias correction is used.

Every day must satisfy stock and demand balance. Cumulative ordered minus received
units must equal outstanding orders. The run covers nine scenarios, two policies,
50 products, and 28 days: 25,200 ledger rows. Orders due beyond the horizon remain
visible in final on-order inventory.

## 5. Demonstrate the interface

1. **Overview:** begin with the default 95% threshold. Both policies miss it. Read
   the stock and fill changes together rather than presenting the reduction alone.
2. **Planning context:** change lead time to three days. The qualifying policy
   comparison changes, but the threshold does not regenerate forecasts or buffers.
3. **Inventory:** compare the nine-scenario chart and inspect service exceptions.
   The CSV download contains only the current pair's aggregate metrics.
4. **Demand:** show the training-period trend and long zero-sales runs. A zero run
   cannot establish a stockout without actual availability records.
5. **Forecasts:** switch validation to final evaluation, then filter one product.
   Scores change with the cohort; the original full-cohort selection does not.

## 6. Explain what would change in production

Actual stock balances, purchase orders, receipts, supplier lead-time distributions,
assortment dates, and acquisition/holding/shortage costs would support a more useful
operational model. A longer replay with a warm-up would reduce sensitivity to the
initial pipeline. Rolling reforecasting would also require careful handling of
sales censored by stock availability.

Before deployment, a business service/cost objective and a fresh evaluation plan
would be needed. Public hosting and native Power BI/RDL artifacts are not part of
this completed Python publication package.

## Reproduce or inspect

| Entry point | Output / purpose |
| --- | --- |
| `scripts/build_data.py` | validated daily mart and input profile |
| `scripts/backtest.py` | validation forecasts, diagnostics, local selection record |
| `scripts/evaluate.py` | frozen final-period comparison |
| `scripts/simulate.py` | daily stock ledgers, per-product metrics, aggregate scenario results |
| `app/streamlit_app.py` | four-view decision dashboard |
| `tests/` | accounting, leakage, decision-rule, and interaction checks |

[Setup](SETUP.md) · [Architecture](ARCHITECTURE.md) · [Source notes](DATA_SOURCES.md)
