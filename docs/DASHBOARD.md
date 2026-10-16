# Decision dashboard

The dashboard connects inventory tradeoffs to the sales and forecast evidence
behind them. Four views keep the planning summary separate from detailed analysis.

## Views

| View | Question | Main outputs |
| --- | --- | --- |
| Overview | Which displayed policy meets the planning preference with less stock? | Conditional decision summary, inventory/fill changes, policy metrics, stock trajectory |
| Inventory | How do lead time and starting stock change the tradeoff? | Nine-scenario chart, policy comparison, product service exceptions, aggregate CSV export |
| Demand | What do observed sales patterns look like? | Training-period units/value, weekly sales, product contributions, zero-sales runs |
| Forecasts | What evidence supports the selected forecast? | Cohort-level validation/final scores and product-level predicted versus observed sales |

## Filter behavior

The Planning context sidebar contains lead time, starting-stock cover, the
fill-rate threshold, and product selection. Scenario inputs affect Overview and
Inventory. Product selection applies to every view, including forecast scores,
scenario comparisons, service exceptions, and demand totals.

The fill-rate threshold is a planning preference over the displayed results.
It does not regenerate forecasts, change the simulation's buffer, or optimize a
policy. Among alternatives meeting the threshold, the decision summary identifies
the one with lowest average closing stock. If neither qualifies, it says so.
Equal-stock and zero-demand cases do not produce a false reduction or fill rate.

The default context is the seven-day lead, 14-day starting-stock case. At the
95% threshold, neither policy qualifies: simulated fill is 94.83% for fixed cover
and 93.88% for order-up-to. Order-up-to's 17.7% inventory reduction is shown beside
its 0.96 percentage-point fill reduction rather than as an unqualified benefit.

## Interpretation

Inventory is a retrospective simulation using observed sales as requested units.
Stock, supplier inputs, and the safety buffer are hypothetical. No monetary
objective or actual retailer savings is estimated. Orders beyond the replay's end
remain in the final on-order figure. The method has no warm-up interval.

Demand charts use the initial training history only. Sales value uses selling
prices; it is neither profit nor acquisition cost. Zero-sales runs cannot identify
stockouts. Forecast scores recalculate for the selected products, while the frozen
full-cohort selection remains unchanged. The final period has already been inspected.

The Inventory download contains only aggregate metrics for the current policy pair.
It does not export daily source observations or forecasts.

## Presentation and verification

The application uses a light theme, consistent policy colors, short metric labels,
explicit units, and tooltips. Charts expose dates and quantities on hover. Detailed
assumptions and source notes are available in expandable sections.

Desktop visual review covered all four views on 2026-10-16. Local integration
checks cover navigation, final-period switching, scenario changes, threshold changes,
product filters, and empty selection. Unit checks cover service constraints,
undefined percentage changes, equal-stock comparisons, and volume-weighted forecast
scores. The full local suite contains 28 unit checks and three dashboard integration
checks. The integration checks skip when the local analysis has not been built.

## Run

```sh
.venv/bin/python -m streamlit run app/streamlit_app.py
.venv/bin/python -m unittest discover -s tests -v
```

The application reads local generated outputs. Public deployment and publication
screenshots are separate release tasks.
