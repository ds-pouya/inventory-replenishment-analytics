# Implementation status — 2026-10-15

## Completed and verified locally

- Downloaded the three M5 inputs from the explicitly approved university mirror;
  provider size/MD5 checks passed and SHA-256/source metadata recorded locally.
- Profiled 30,490 sales series, 1,969 calendar rows and 6,841,121 weekly prices.
- Built a 50-product CA_1 / FOODS_3 mart with 97,050 item-day observations,
  covering 2011-01-29 through 2016-05-22.
- Reconciled joined row counts and unit totals; no missing prices on positive sales.
- Found 6,111 unpriced zero-sales rows; they remain explicit missing
  prices, not zero-priced merchandise or observed stockouts.
- Ran two baseline forecasts across four 28-day validation windows.
- Seven synthetic-data tests passed; real-data Streamlit checks passed for the full
  cohort, empty selection and a single product. Dependencies pass pip check.
- Started local preview at http://127.0.0.1:8503.

## Initial validation result

| Model | MAE (units per item-day) | Aggregate WAPE |
| --- | ---: | ---: |
| Previous-week pattern | 6.866 | 50.10% |
| Recent 28-day mean | 6.379 | 46.55% |

The recent mean has 7.1% lower MAE on these validation windows. This is
an initial baseline comparison on the selected active-product cohort, not a
final test result or an inventory benefit. The final 28-day holdout is excluded
from backtesting. Its records are loaded for quality checks, not used for model
selection or the demand overview. No tuned model has been evaluated on it.

## Next milestone

Add a calendar-aware forecasting candidate and investigate long zero-sales runs
without claiming stockouts. Freeze the model-selection rule before final evaluation.
Then implement and validate inventory-policy simulation with explicit assumptions.

Inventory simulation, public app deployment, and native BI reports remain future work.
The source repository is being initialized with this implementation as its first commit.
