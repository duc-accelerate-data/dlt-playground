"""Verify against starter.py instead of solution.py.

Lets you check your own work in starter.py without touching solution.py.
The reference solution stays untouched as a peek-when-stuck fallback.
"""
import os
import runpy
from pathlib import Path

os.environ["EXERCISE_SOURCE"] = "starter.py"
runpy.run_path(str(Path(__file__).resolve().parent / "verify.py"), run_name="__main__")
