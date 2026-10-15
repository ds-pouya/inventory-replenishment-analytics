# Forecast evaluation

## Candidate models

I compare three models with the same 28-day forecast horizon and the same product
cohort. Every forecast is issued once at the window's start; observations arriving
inside the window do not update it.

| Model | Method |
| --- | --- |
| Previous-week pattern | Repeat the last seven observed daily sales values |
| Recent daily average | Repeat the mean of the last 28 observed days |
| Calendar ridge | Regularized regression fitted separately to each product's most recent 364 days |

The calendar model uses six weekday indicators, annual sine and cosine terms,
a linear trend, the store state's SNAP flag, and an indicator for any listed event.
These calendar inputs are known for the target dates. No future realized prices,
sales, rolling sales features, or inventory measurements enter the design matrix.

The intercept is unpenalized; other coefficients use a fixed ridge penalty of 10.
Predictions are clipped at zero. The training window and penalty are fixed in
`config/forecasting.toml`, rather than tuned against the final period. The model
estimates observed sales; it does not recover unobserved demand.

## Selection rule and timing

The four validation windows cover days 1802–1913. Pooled mean absolute error across
all 5,600 product-days determines the winner. A model-name sort breaks exact ties.
All candidates share the same observations, so aggregate WAPE produces the same
ranking; individual-product rankings may differ.

`docs/FORECAST_SELECTION.json` records the selected model, validation scores, and
hashes of the configuration, build configuration, source calendar, daily mart, and
forecast implementation. This record is committed before final evaluation.
The evaluation command rejects inputs or forecasting code that differ from it.

The final period is days 1914–1941. The selected model is refitted using observations
through day 1913. All three fixed candidates are scored for comparison, but the
selected model is retained regardless of which performs best on that period.
A rerun reproduces the same evaluation; it is not another independent experiment.
The final period is considered inspected after this milestone and cannot serve
as an untouched test for later model changes.

## Metrics

MAE reports absolute error per product-day. Aggregate WAPE is total absolute error
divided by total actual sales; it is undefined when actual sales total zero. Bias
is mean predicted minus actual sales, so a positive value indicates overprediction.

These scores cover 50 active products in one store and department. They do not
establish performance across the entire M5 hierarchy or inventory cost savings.

## Zero-sales diagnostics

The diagnostic report uses only days 1–1801. It records each product's zero-sales
share, longest zero-sales run, runs lasting at least 28 days, and leading/trailing
zero days. These describe observed sales history. Product introductions, demand,
assortment changes, closures, and stock availability can all affect zero sales;
these records cannot distinguish their causes.

## Reproduction

```sh
.venv/bin/python scripts/backtest.py
.venv/bin/python scripts/evaluate.py
```

Backtesting regenerates local validation outputs. Final evaluation uses the tracked
selection record; changing the model specification requires a new development
experiment and an evaluation plan that acknowledges the inspected final period.
