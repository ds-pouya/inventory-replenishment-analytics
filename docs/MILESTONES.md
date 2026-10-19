# Milestones

- [x] Define the inventory-planning scope and assess the M5 source.
- [x] Create a local project structure and initial design documentation.
- [x] M1: verify acquisition/terms, fingerprint inputs, profile schemas and coverage.
- [x] M2: build reproducible sales/price/calendar marts and reconcile joins/totals.
- [x] M3: complete forecasting candidate comparison and frozen final evaluation.
  - [x] Compare two baselines and a calendar-aware regression on validation windows.
  - [x] Commit the selection record before final scoring; report holdout outcomes.
  - [x] Diagnose training-period zero-sales runs.
- [x] M4: implement baseline and order-up-to simulations with flow checks.
  - [x] Compare nine lead-time/initial-stock scenarios and verify deterministic reruns.
- [x] M5: complete the decision dashboard including replenishment simulation.
  - [x] Run demand overview and forecast diagnostics; check default, empty and single-product filters.
  - [x] Integrate simulation scenario comparison and product filtering.
  - [x] Finish decision summaries, presentation layout, and desktop visual review.
  - [x] Verify product-filter consistency, service-threshold logic, and aggregate exports.
- [x] M6: publish findings, screenshots, and a technical walkthrough.
  - [x] Lead the repository README with the business question and measured results.
  - [x] Capture all four dashboard views and record their context and file hashes.
  - [x] Document the full analytical sequence and an end-to-end demonstration.
- [ ] M7: add Power BI/PBIR/model and RDL only with target-runtime validation.
  - [x] Author PBIP/PBIR/TMSL and parameterized RDL sources; check schemas and local extracts.
  - [ ] Validate native model refresh, DAX, report interactions, pagination, and exports.

- [ ] M8: launch a distributable public dashboard demo.
  - [x] Generate and label independent synthetic data; test clean-copy startup and interactions.
  - [x] Add deployment settings, repository CI, and a launch draft.
  - [ ] Deploy publicly, verify signed-out access, and publish the confirmed live link.

Release criteria include a reproducible setup, code licensing, source attribution,
completed validation, and documented limitations. Raw data and credentials remain
outside version control.
