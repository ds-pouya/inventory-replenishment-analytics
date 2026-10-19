# Distributable synthetic example

These files are generated independently by `src/inventory_analytics/demo.py`
with seed **20261019**. They contain 24 invented products at `DEMO_STORE`, using
Poisson sales, weekly/annual patterns, promotion effects, mild trends, and
explicit intermittent/zero-sales periods. Price levels and all generating
parameters are declared in code or sampled from declared distributions.

No M5 rows, retailer identifiers, or parameters fitted to M5 are included.
The demo uses the same forecasting and inventory functions as the local case
study, with its own data, validation-first selection, and results. Its selection
record is created before synthetic final scoring in a disposable build directory;
it does not replace the separately committed M5 selection record.

The bundle contains the eight outputs needed by the read-only dashboard and a
SHA-256 manifest. It is approximately 0.6 MB and runs without downloads, source
credentials, or a local analysis build. `manifest.json` records the generator hash
and NumPy version. Regenerate with `python scripts/build_demo.py` using the locked
dependencies; floating-point or serialization differences across platforms may
change file hashes. The checked-in manifest describes the shipped files.

The repository's MIT license covers this generated synthetic example. It does
not grant rights to the separate M5 source data. Metrics here demonstrate the
workflow and must not be presented as the published M5 case-study results.
