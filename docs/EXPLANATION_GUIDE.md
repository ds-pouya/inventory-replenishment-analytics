# Methodology and interpretation

## Why this case study?

It joins industrial engineering inventory decisions with data modeling and
forecast evaluation. It examines which active product-store series deserve
planning attention and how replenishment policies trade simulated service against
inventory under documented assumptions.

## Why three input tables?

Sales are wide: each product-store row has one column per day. We reshape that
to one row per item, store and day. Calendar translates the day key into dates
and weeks. Prices join on item, store and week. Checking uniqueness prevents a
price join from multiplying sales and inflating reported revenue.

## Why use a subset?

The full sales table reshapes to roughly 59 million observations. Start with 50
active products in one department/store, chosen by training-period unit sales.
That is inexpensive to iterate on and reproducible, but favors active products.
It does not establish performance for intermittent or slow-moving products.

## What is leakage?

Using future information to choose products, features or model parameters can
make historical performance look better than a real forecast. Selection ends
at day 1801. Each validation forecast sees only its preceding history. The
final 28-day evaluation period was scored only after the selection record was
committed. It is now inspected and cannot serve as an untouched test for later changes.

## What do the first forecasts mean?

Seasonal naive repeats the last observed seven days, preserving weekday shape.
The 28-day mean predicts the same recent-average daily volume throughout the
forecast horizon. Both forecast the entire next 28 days at once, without using
actual sales that arrive inside that horizon.

MAE is the average absolute unit error per item-day. Aggregate WAPE divides
summed absolute errors by summed actual units; high-volume items influence it
more. Neither proves an inventory policy saves money. Zero-total windows have
undefined WAPE and are recorded as null, not zero.

## Which conclusions are unavailable?

Zero sales might mean no demand or unavailable inventory. M5 cannot tell us
which. Selling prices do not tell us acquisition costs or profit. Lead times,
stock balances and service improvements must be labeled scenario assumptions
and simulation outcomes rather than actual retailer operations.

## Why did the selected model lose on the final period?

Validation chooses a model using earlier windows; it cannot guarantee the same
ranking on a later window. Calendar ridge had the lowest validation MAE, but the
recent average performed better on the final holdout. The selection remains
unchanged, preserving an honest estimate of that decision's performance. Neither
result alone determines the best inventory policy: service and inventory outcomes
also depend on lead times, uncertainty, and replenishment rules.

## How do the inventory policies differ?

Fixed cover orders one review period of pre-start average sales every seven days,
regardless of available stock. Order-up-to subtracts on-hand and incoming stock
from a forecast target plus a safety buffer. Subtracting incoming orders prevents
reordering stock already in transit. Receipts arrive before review and demand.

The base case uses less inventory under order-up-to but has more unmet units.
That is a tradeoff requiring a service/cost objective, not evidence of savings.
The normal-quantile buffer uses approximate independent-error assumptions, so its
nominal 95% parameter does not guarantee a 95% simulated unit fill rate.
