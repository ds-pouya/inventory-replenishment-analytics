# Inventory simulation results — 2026-10-15

## Scope

This deterministic replay uses observed sales as requested units for 50 products
over days 1914–1941. Both policies see the same demand proxy and start with identical
inventory within each scenario. Stock, lead times, and supplier behavior are
hypothetical. The scenarios and engine were committed in `aca1d75` before the first run.

The forecast model remains the calendar ridge model selected before final
forecast evaluation. Simulation targets are not retuned using these replay results.
The period was already inspected during forecasting, so this comparison is
retrospective. It does not measure actual retailer service, savings, or causality.

## Base scenario

Seven-day lead time, seven-day review period, and 14 days of initial stock cover.
Initial stock uses the pre-replay recent mean; the supplier pipeline starts empty.

| Measure | Fixed-cover baseline | Order-up-to |
| --- | ---: | ---: |
| Simulated unit fill rate | 94.83% | 93.88% |
| Average closing inventory (units) | 7,292.3 | 5,998.1 |
| Unmet units | 1,084 | 1,285 |
| Shortage item-days | 69 | 82 |
| Orders placed | 200 | 190 |
| Units ordered | 19,800 | 17,836 |
| Final on-hand units | 4,827 | 3,142 |
| Final on-order units | 4,950 | 4,872 |

Order-up-to held 17.7% less average closing inventory, with a
0.96 percentage-point lower simulated fill rate and
201 additional unmet units. Neither policy dominates on both measures.

There is no cost function or business-approved service constraint, so these
outcomes do not identify an economically optimal policy. A planner would need to
weigh inventory requirements against acceptable unmet demand. The 95% nominal
buffer parameter is not a guaranteed 95% unit fill rate.

## Sensitivity scenarios

All scenarios use seven-day reviews. Inventory is mean closing on-hand stock summed
across products. The grid was fixed before running; no scenario is presented as
an optimized recommendation.

| Lead days | Initial cover days | Fixed fill | Order-up-to fill | Fixed inventory | Order-up-to inventory |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 7 | 94.73% | 95.85% | 5,248.6 | 4,732.9 |
| 3 | 14 | 96.04% | 95.97% | 10,056.6 | 5,567.8 |
| 3 | 28 | 96.69% | 97.32% | 19,824.9 | 10,836.2 |
| 7 | 7 | 88.22% | 92.18% | 3,001.1 | 4,831.5 |
| 7 | 14 | 94.83% | 93.88% | 7,292.3 | 5,998.1 |
| 7 | 28 | 96.42% | 95.27% | 17,022.3 | 10,932.2 |
| 14 | 7 | 67.47% | 72.16% | 1,990.6 | 6,175.0 |
| 14 | 14 | 88.19% | 90.20% | 4,149.6 | 6,100.5 |
| 14 | 28 | 96.05% | 95.42% | 13,348.6 | 11,155.9 |

## Verification and limits

- 25,200 daily product-policy-scenario records cover all nine scenarios and two policies.
- Daily stock and demand balances and cumulative stock/pipeline balances reconcile.
- Repeating the run produces the identical summary, including input fingerprints.
- Twenty-one tests cover forecasting, data validation, delivery timing, orders in
  transit, lost sales, zero demand, cohort aggregation, invalid inputs, and earlier
  decisions remaining independent of later replay demand.
- Dashboard checks cover base-case values, scenario changes, product filters, and
  empty selections.

The short horizon and empty initial pipeline create startup effects. Orders due
after the replay remain visible as final on-order inventory. There is no warm-up,
steady-state result, lead-time uncertainty, or purchase/holding/shortage cost.
The policy bundles differ in forecast, buffer, and stock-position control; the
comparison cannot isolate the contribution of each component. Normal independent
error assumptions used for buffer sizing are approximate.

See [simulation methodology](SIMULATION.md) for event timing, formulas, and
provenance. [Aggregate run record](SIMULATION_RESULTS.json) preserves all scenario
metrics and fingerprints without publishing source observations or daily ledgers.
