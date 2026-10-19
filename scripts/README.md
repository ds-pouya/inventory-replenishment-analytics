Run download_data.py, build_data.py, backtest.py, evaluate.py, then simulate.py. Evaluation and simulation verify frozen forecasting inputs. See docs/SETUP.md, docs/FORECASTING.md, and docs/SIMULATION.md.

`build_native_reports.py` exports the simulation ledger, reconciles all scenario-policy
results, and regenerates PBIP/PBIR/TMSL and RDL sources. `validate_native_reports.py`
checks public JSON schemas and RDL XSD; it does not execute a Power BI runtime.
See `reports/VALIDATION.md` and the native report READMEs.
