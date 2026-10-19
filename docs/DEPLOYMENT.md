# Public demo deployment

## Package status

The public entry point is `app/demo_app.py`. It always reads the checked-in
synthetic bundle under `data/demo/`, even when local M5 outputs exist.
`app/streamlit_app.py` remains the local M5-analysis entry point.
The public bundle requires no runtime data download, secrets, or analytical rebuild.

The original M5 results and screenshots remain in the repository. The public
demo has 24 invented products and different metrics; every view labels that
provenance. [Bundle description](../data/demo/README.md).

Local verification on 2026-10-19: 38 checks passed, including a clean-copy public
app run without raw data or M5 outputs. Public hosting is pending deployment;
no live URL is claimed here.

## Streamlit Community Cloud settings

| Setting | Value |
| --- | --- |
| Repository | `ds-pouya/inventory-replenishment-analytics` |
| Branch | `main` |
| Main file | `app/demo_app.py` |
| Python | `3.13` in Advanced settings |
| Dependencies | Root `requirements.txt` |
| Secrets | None |
| Suggested subdomain, subject to availability | `pouya-inventory-planning` |

Sign in at [Streamlit Community Cloud](https://share.streamlit.io/), select
**Create app**, and enter the settings above. Use public-app visibility for
portfolio sharing. Review the hosting service's current account terms and GitHub
permissions during setup. No paid infrastructure is required by this design.

The root requirements pin the direct application dependencies. The complete
`requirements-lock.txt` records the tested environment and is used by repository
CI. Select Python 3.13 explicitly before deploying; the service's default can
be different. [Official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Verify the deployed app

1. Confirm startup completes and a synthetic-data notice appears immediately.
2. Visit Overview, Inventory, Demand, and Forecasts. Change lead time, starting
   cover, service threshold, and products; check the empty-selection message.
3. Inspect both forecast periods and a single product. Download the policy CSV
   and verify the selected scenario and numbers match the displayed table.
4. Check a narrow screen for readable controls and horizontal table scrolling.
5. Open the resulting public URL while signed out. Record the actual URL and
   deployed commit below, then add that verified link to the GitHub README,
   repository website field, and launch draft.

| Deployment record | Value |
| --- | --- |
| Public URL | Pending |
| Deployed commit | Pending |
| Public smoke test | Pending |

## Local demo and regeneration

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m streamlit run app/demo_app.py
```

Regenerate only when changing the synthetic example:

```bash
.venv/bin/python scripts/build_demo.py
.venv/bin/python -m unittest discover -s tests -v
```

The generator reuses the existing validation, forecasting, and simulation
functions inside a disposable directory. It never overwrites local M5 artifacts
or the committed M5 selection record. Review and commit regenerated bundle
files together with their manifest. Runtime hosting serves the committed bundle;
it does not regenerate data on startup.

Repository CI uses read-only GitHub permissions and runs the unit/integration
suite on Python 3.13. The three local M5 dashboard checks skip when local analysis
is absent; the public demo checks run on every clean checkout.
