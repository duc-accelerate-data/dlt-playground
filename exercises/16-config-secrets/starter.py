"""Exercise 16 — multi-tenant credentials via section= / with_args()."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.github_source import github_source

# Expects .dlt/secrets.toml:
#   [sources.github_a]
#   access_token = "..."
#   [sources.github_b]
#   access_token = "..."

# TODO: build two pipelines, each using github_source.with_args(section=...) with a distinct dataset.
