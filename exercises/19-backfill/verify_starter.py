"""Verify against starter.py instead of solution.py."""
import os
import runpy
from pathlib import Path

os.environ["EXERCISE_SOURCE"] = "starter.py"
runpy.run_path(str(Path(__file__).resolve().parent / "verify.py"), run_name="__main__")
