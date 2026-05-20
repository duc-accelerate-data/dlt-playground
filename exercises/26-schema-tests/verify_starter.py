"""Run this exercise's verifier against starter/ instead of solution/."""
import os, runpy
from pathlib import Path
os.environ["EXERCISE_SOURCE"] = "starter"
runpy.run_path(str(Path(__file__).resolve().parent / "verify.py"), run_name="__main__")
