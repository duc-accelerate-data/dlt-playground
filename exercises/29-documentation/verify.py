"""Verify exercise 29."""
import os
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done

EX = Path(__file__).resolve().parent
SRC = os.environ.get("EXERCISE_SOURCE", "solution")
SOLUTION = EX / SRC / "solution.py"
RUNBOOK = EX / SRC / "RUNBOOK.md"

header("29-documentation")
if not SOLUTION.exists():
    check(False, f"no solution.py at {SOLUTION}")
    done()
ns = runpy.run_path(str(SOLUTION), run_name="__exercise__")
pipeline = ns["pipeline"]
repos_resource = ns["repos"]

# 1. Docstring covers source/auth/cursor.
doc = (repos_resource.__doc__ or "").lower()
check(len(doc) >= 100, f"resource docstring ≥ 100 chars (got {len(doc)})")
for term in ("source", "auth", "owner"):
    check(term in doc, f"docstring mentions '{term}'")

# 2. Column descriptions present for the 4 named columns.
cols = pipeline.default_schema.get_table("repos")["columns"]
for c in ("id", "name", "full_name", "updated_at"):
    desc = cols.get(c, {}).get("description", "")
    check(bool(desc), f"column `{c}` has a description ('{desc[:60]}...')")

# 3. RUNBOOK.md exists with required sections.
check(RUNBOOK.exists(), "RUNBOOK.md exists")
text = RUNBOOK.read_text() if RUNBOOK.exists() else ""
check(len(text) >= 200, f"RUNBOOK.md ≥ 200 chars (got {len(text)})")
for term in ("Backfill", "Rollback", "Owner"):
    check(term in text, f"RUNBOOK.md mentions '{term}'")

# 4. Round-trip — descriptions survive in pipeline.default_schema.to_pretty_yaml().
yaml_dump = pipeline.default_schema.to_pretty_yaml()
check("Server-side last-modified timestamp" in yaml_dump,
      "column descriptions round-trip into the schema YAML export")

done()
