# Native Power BI source

**Status: source and JSON schemas checked; Desktop load, Power Query refresh,
DAX execution, interactions, and rendering are unverified.**

Open `Inventory.pbip` in Power BI Desktop when a Windows environment is available.
The project contains an enhanced PBIR report and a TMSL `model.bim` semantic model.
TMSL keeps this small model in a single JSON definition; it is a supported PBIP
model format alongside TMDL. No PBIX binary is included.

## Data and model

Run from the repository root after the simulation:

```bash
.venv/bin/python scripts/build_native_reports.py
.venv/bin/python scripts/validate_native_reports.py
```

The build exports five local CSV tables to `data/processed/native/`: a 25,200-row
Ledger fact and Scenario (9), Policy (2), Product (50), and Date (28) dimensions.
The CSV files and their SHA-256 manifest remain ignored by Git. They contain
analysis derived from the local M5 inputs and must follow the source terms.

The model uses four single-direction, many-to-one relationships from Ledger to
the dimensions. Numeric fact columns are hidden; explicit measures define the
aggregation. Unit fill is total fulfilled units divided by total sales-proxy
units. Average closing inventory is the mean of daily **cohort totals**, rather
than the mean of product rows or a sum over days.

Measures default to `L7_R7_I14` when Scenario is unfiltered. A single selected
scenario overrides that default; multiple scenarios produce blank measures.
Policy must resolve to one value, as it does in a table row or chart series.
Policy grand totals remain blank because the policies represent alternatives.
The same historical sales must not be added across alternative policies/scenarios.
Dates can restrict the simulated period, and Product selections restrict the
cohort. The scenario selector uses IDs: `L` = lead-time days, `R` = review days,
`I` = initial-stock cover days. The report contains:

- **Policy comparison:** scenario/product selectors, policy metrics, daily stock trend.
- **Product exceptions:** scenario/product selectors and product-policy metrics.
  The RDL report provides the list restricted to products with unmet proxy units.

## Desktop acceptance procedure

1. Copy the five local CSV files to the validation machine. Open `Inventory.pbip`.
   Enable the applicable PBIP feature if required by the installed Desktop release.
2. Change the `DataFolder` Power Query parameter to their containing directory,
   using forward slashes, for example `C:/inventory-data/native`. Refresh.
3. Confirm the row counts above, dimension uniqueness, and four relationships.
   Run `Inventory.SemanticModel/DAXQueries/Acceptance.dax` in DAX query view.
4. With no scenario filter, the policy table must show approximately:

   | Policy | Unit fill | Average closing inventory | Unmet proxy units |
   | --- | ---: | ---: | ---: |
   | fixed_cover | 94.8349% | 7,292.3214 | 1,084 |
   | order_up_to | 93.8772% | 5,998.1429 | 1,285 |

5. Select each scenario and compare with `docs/SIMULATION_RESULTS.json`.
   Test one product, multiple products, all products, one date, and multiple
   scenarios. Multiple scenarios and policy totals must not yield inflated sums.
6. Check both pages, slicer interactions, date ordering, labels, table totals,
   keyboard order, and export. Save, close, reopen, and refresh again.
7. Record Desktop version, date, failures/corrections, and actual screenshots in
   the validation record before describing the report as runtime validated.

The build regenerates report/model definitions. Preserve any Desktop edits before
rerunning it, or implement the edits in the generator. Keep local model caches,
credentials, tenant details, and CSV data outside version control.

## References

- [PBIP report/PBIR structure and schemas](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Semantic model files and TMSL/TMDL formats](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset)
- [Microsoft JSON schemas](https://github.com/microsoft/json-schemas)
