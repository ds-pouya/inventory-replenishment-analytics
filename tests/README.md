Synthetic fixtures cover source validation, forecast isolation and frozen evaluation, inventory receipt/review timing, orders in transit, lost sales, zero demand, rounding, cohort metrics, invalid inputs, and decision timing. Presentation tests cover decision constraints and undefined metrics; local dashboard integration checks cover navigation and filter consistency and skip without generated data.

`test_demo.py` checks shipped synthetic-data hashes, grain/accounting, repeatable
source generation, and all public app views in a clean copy without M5 outputs.
These checks run in GitHub Actions; the three M5 app checks require local data.
