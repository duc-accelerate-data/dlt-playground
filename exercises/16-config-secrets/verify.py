"""Verify exercise 16 — requires sections github_a / github_b configured in .dlt/secrets.toml."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.verify import header, check, done, run_solution, table_exists

header("16-config-secrets")
have_a = os.environ.get("SOURCES__GITHUB_A__ACCESS_TOKEN")
have_b = os.environ.get("SOURCES__GITHUB_B__ACCESS_TOKEN")
secrets = Path(__file__).resolve().parents[2] / ".dlt" / "secrets.toml"
toml_has_sections = secrets.exists() and "[sources.github_a]" in secrets.read_text() \
    and "[sources.github_b]" in secrets.read_text()

if not (toml_has_sections or (have_a and have_b)):
    print("  ⚠ SKIP: configure [sources.github_a] / [sources.github_b] in .dlt/secrets.toml "
          "or set SOURCES__GITHUB_A__/B__ACCESS_TOKEN env vars to verify.")
    sys.exit(0)

run_solution(__file__)

check(table_exists("bronze_github_a", "repos"), "github_a repos loaded under its own section")
check(table_exists("bronze_github_b", "repos"), "github_b repos loaded under its own section")
done()
