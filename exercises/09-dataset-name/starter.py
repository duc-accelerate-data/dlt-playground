"""Exercise 09 — env-driven dataset name."""
import os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt
from shared.chess_source import chess_source

# TODO: read env DLT_ENV (default "dev"). Build dataset_name "bronze_chess_<env>".
# TODO: run the chess source through that pipeline. Print which dataset it wrote to.
