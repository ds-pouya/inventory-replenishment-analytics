# Forecasting results — 2026-10-15

## Evaluation scope

50 products at CA_1 / FOODS_3, selected using days 1–1801. Four validation windows
cover 5,600 product-days; the final window covers 1,400 product-days. All models
forecast the full 28-day horizon from a common origin.

## Validation results

| Model | MAE (units per product-day) | Aggregate WAPE |
| --- | ---: | ---: |
| calendar_ridge | 6.101 | 44.51% |
| mean_28 | 6.379 | 46.55% |
| seasonal_naive_7 | 6.866 | 50.10% |

Calendar ridge was selected by lowest pooled validation MAE. The specification
and selection record were frozen in commit `212c40a` before the final evaluation.
The model uses a 364-day training window, weekday/annual/trend terms, SNAP days,
and an event indicator with a fixed ridge penalty of 10.

## Final holdout results

| Model | MAE (units per product-day) | Aggregate WAPE | Mean bias (units) |
| --- | ---: | ---: | ---: |
| calendar_ridge | 6.060 | 40.42% | +0.283 |
| mean_28 | 5.911 | 39.43% | -0.896 |
| seasonal_naive_7 | 5.992 | 39.97% | -1.116 |

The recent 28-day average has the lowest error on the final period. Calendar ridge
remains the validation-selected model; the final results do not trigger reselection.
This reversal shows that lower validation error did not produce a final-period
improvement in this case. The calendar model has less negative bias, but that
does not establish a better inventory policy. No cost or service improvement has
been measured. Positive bias means predicted sales exceed actual sales on average.

The final period has now been inspected. Any later model changes need evaluation
on additional periods or a clearly labeled retrospective comparison. This single
28-day window does not establish performance across stores, seasons, or retailers.

## Zero-sales history

Training-only diagnostics found runs of at least 28 zero-sales days in 36 of the
50 products. The longest run is 914 days; 16 products have leading zero-sales days.
Product introductions, assortment changes, demand and availability are possible
explanations, but the source cannot distinguish them. The cohort and split remain
unchanged; the analysis does not remove difficult series after seeing final scores.

## Verification

- Twelve automated tests cover data integrity, forecast leakage, zero-denominator
  metrics, zero-run boundaries, weekday learning, and frozen-input enforcement.
- Streamlit checks cover validation/final-period switching, product filtering,
  and empty selections.
- Raw data, per-observation forecasts, and generated diagnostics remain local.
  Only aggregate findings and the selection fingerprints are published.
