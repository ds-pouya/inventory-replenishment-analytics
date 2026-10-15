# Inventory policy simulation

## Objective and scope

I compare a fixed-cover replenishment baseline with a forecast-based order-up-to
policy on the 50-product cohort. The replay covers days 1914–1941, the same period
already inspected during forecasting. This is a retrospective scenario analysis,
not an independent test of a newly selected inventory policy.

Observed sales are treated as requested units in the simulator. Actual inventory,
orders, lead times, acquisition costs, and unmet demand are unavailable. The
simulation therefore cannot estimate actual retailer stockouts or financial savings.

## Daily event sequence

The simulation starts with no orders in transit. For each product and day:

1. Record opening stock and receive orders due that morning.
2. Review inventory at the start of day 1 and every R days afterward.
3. Place any replenishment order; an order on day t arrives before demand on t + L.
4. Fulfill requested units from available stock.
5. Record unmet units as lost sales, with no backlog or substitution.
6. Record closing stock and all outstanding replenishment orders.

Receipts precede both review and demand. A one-day lead time means next-morning
delivery. Lead time and review period must be positive whole days. All stock and
orders are whole units. Targets and starting stock are rounded upward.

The engine checks these identities every day:

- Opening stock + receipts - fulfilled units = closing stock.
- Requested units = fulfilled units + lost units.
- Initial stock + cumulative receipts - cumulative fulfillment = closing stock.
- Cumulative orders - cumulative receipts = outstanding orders.

## Common inputs

Both policies use the same demand replay, initial stock, review schedule, and lead
time within each scenario. Initial stock is the mean observed daily sales over the
28 days before the replay multiplied by the configured starting-stock cover.
There is no initial supplier pipeline or warm-up interval.

The default scenario has a seven-day lead time, seven-day review period, and
14 days of initial stock cover. Sensitivities cross lead times of 3, 7, and 14 days
with starting-stock cover of 7, 14, and 28 days. These inputs are hypothetical and
are fixed in `config/scenarios.toml` before the first simulation run.

## Fixed-cover policy

Every review places the same quantity: the ceiling of the pre-replay 28-day mean
daily sales multiplied by R. This covers one review period of historical average
sales. The quantity does not respond to on-hand stock, outstanding orders, forecast
changes, or unmet units. This intentionally simple baseline may accumulate stock
or leave shortages when demand differs from that average.

## Order-up-to policy

Inventory position is on-hand stock plus orders in transit. At an opening review,
the protection interval covers today's demand and the next L + R - 1 days. The
order quantity is the positive difference between a target and inventory position:

```text
protection days = lead time + review period
safety buffer = z × daily residual standard deviation × sqrt(protection days)
target = ceil(sum of forecasts over protection days + safety buffer)
order = max(0, target - on-hand stock - on-order stock)
```

The forecasts use the calendar ridge model selected in the forecasting milestone.
They are issued once at day 1913 and remain fixed throughout the replay. Known
calendar rows extend predictions beyond the replay so that late reviews still
have a complete protection interval. Future sales are absent from these extra
calendar rows and do not enter the prediction calculation.

The residual standard deviation is estimated separately for each product using
its 112 pre-replay validation errors. The nominal service parameter of 0.95 gives
a one-sided standard-normal z value of approximately 1.645. Square-root scaling
assumes independent daily errors; normality, constant variability, and negligible
bias are approximations. Correlation, intermittent sales, and biased forecasts
can invalidate that coverage interpretation. There is no fitted bias correction.
The nominal parameter sizes a buffer and is not a guarantee of cycle service or
unit fill rate.

Periodic-review protection over lead time plus review time follows the inventory
framework in [MIT's Supply Chain Planning summary](https://ocw.mit.edu/courses/15-763j-manufacturing-system-and-supply-chain-design-spring-2005/e1800430fdccaf618b22bd551fc00fac_summary.pdf).

## Comparison and metrics

This compares policy bundles: the order-up-to alternative combines inventory-position
control, calendar forecasts, and a safety buffer, while the baseline uses fixed
historical-average quantities. Differences cannot be attributed to any single
component. No policy is optimized using the replay outcomes.

Unit fill rate is total fulfilled units divided by total requested units; a
zero-demand cohort has an undefined fill rate. Average closing inventory sums
on-hand units across products for each day, then averages those daily totals.
Shortage item-days count product-days with unmet units, rather than retailer days.
Orders placed, final stock, and final outstanding orders are reported separately.

The 28-day horizon emphasizes initial conditions and late deliveries. There is
no steady-state estimate, salvage value, disposal rule, capacity limit, supplier
uncertainty, or monetary objective. On-order stock is retained in the final report,
including orders arriving after the replay. No stochastic demand draws are used.

## Reproduction and provenance

```sh
.venv/bin/python scripts/simulate.py
```

The command verifies the frozen forecasting inputs and uses the generated
validation forecasts for safety calibration. It writes daily ledgers, product-level
metrics, scenario inputs, and a summary under ignored `data/processed/`. The summary
records configuration and code hashes, calibration fingerprints, and accounting
checks. Only reviewed aggregate results are published in the repository.
