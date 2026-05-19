"""Exercise 10 — subset + apply_hints without editing the source."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.github_source import github_source

src = github_source(org="dlt-hub")
# TODO: src = src.with_resources("issues")
# TODO: src.issues.apply_hints(...)
# TODO: run through a pipeline named "github_subset".
