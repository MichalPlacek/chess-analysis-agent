"""Entry point for launching the Streamlit app."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app = Path(__file__).parent.parent / "app.py"
    sys.exit(subprocess.call(["streamlit", "run", str(app)] + sys.argv[1:]))
