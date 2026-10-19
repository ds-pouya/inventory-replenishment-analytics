"""Public entry point: always use the bundled synthetic example."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('streamlit_app.py')), run_name='__main__', init_globals={'DATA_MODE': 'demo'})
