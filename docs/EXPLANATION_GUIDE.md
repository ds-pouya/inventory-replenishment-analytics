# Explain the first implementation

## Why this case study?

It joins industrial engineering inventory decisions with data modeling and
forecast evaluation. The immediate question is which active product-store
series deserve planning attention. Replenishment recommendations come later,
after forecasts and inventory assumptions have been validated.

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
final 28-day evaluation period is reserved for a later frozen comparison.

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
