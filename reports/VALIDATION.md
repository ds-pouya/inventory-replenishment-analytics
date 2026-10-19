# Native reporting validation record

Source checks run on macOS on 2026-10-19:

| Check | Result |
| --- | --- |
| PBIP, PBISM, PBIR and report/page/visual JSON | 15 documents passed Microsoft JSON schemas |
| InventoryExceptions.rdl | Passed Microsoft RDL 2016/01 XSD with xmllint |
| Local extract | 25,200 rows, unique scenario-policy-product-date grain |
| Extract reconciliation | All 18 scenario-policy pairs match published fill, average stock, and unmet units |
| Automated project tests | 35 passed, including 4 native reporting contract tests |
| Dependency consistency | pip check passed |
| Semantic model engine load / DAX / Power Query | Pending |
| Power BI report rendering / interaction / refresh | Pending |
| RDL provider connection / dataset execution / expressions | Pending |
| Paginated layout / PDF / Excel exports | Pending |

Detailed schema URLs and downloaded schema SHA-256 hashes are written locally to
`outputs/native_schema_validation.json`. CSV hashes are in
`data/processed/native/manifest.json`. Source data and generated extracts are
excluded from Git. The schema checker downloads public Microsoft schemas on its
first run and reuses the local cache. macOS's `xmllint` performs XSD validation.

Source checks establish structural and data-contract consistency. They do not
establish native runtime compatibility. M7 remains open until the pending checks
pass in the target environment; the Streamlit app remains the demonstrated report.
