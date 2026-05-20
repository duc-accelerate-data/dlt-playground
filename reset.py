"""Reset playground state — drops DuckDB schemas + clears dlt pipeline working dirs.

Each exercise is keyed to the datasets and pipeline_names it owns. Running:

    python reset.py             # nuke EVERYTHING (warehouse + all pipeline dirs)
    python reset.py 01          # reset only exercise 01
    python reset.py 01 04 25    # reset multiple
    python reset.py 20-29       # range
    python reset.py --list      # show what each exercise will drop

The warehouse file at data/warehouse.duckdb is shared — when you target a single
exercise, only its datasets are dropped, leaving the file intact.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
WAREHOUSE = REPO / "data" / "warehouse.duckdb"
DLT_HOME = Path.home() / ".dlt" / "pipelines"


# (datasets, pipeline_names) owned by each exercise.
OWNED: dict[str, tuple[list[str], list[str]]] = {
    "01-pipeline":          (["bronze_chess"], ["chess_bronze"]),
    "02-resource":          (["bronze_chess"], ["chess_bronze"]),
    "03-source":            (["bronze_chess"], ["chess_bronze"]),
    "04-schema-contract":   (["bronze_events_evolve", "bronze_events_freeze", "bronze_events_discard"],
                              ["events_bronze_events_evolve", "events_bronze_events_freeze",
                               "events_bronze_events_discard"]),
    "05-write-disposition": (["wd_replace", "wd_append", "wd_merge"],
                              ["wd_replace", "wd_append", "wd_merge"]),
    "06-incremental":       (["bronze_github", "backfill_march"],
                              ["github_bronze_github", "github_backfill_march"]),
    "07-normalize":         (["bronze_chess"], ["chess_bronze"]),
    "08-parent-child":      (["bronze_chess"], ["chess_bronze"]),
    "09-dataset-name":      (["bronze_chess_dev", "bronze_chess_prod"], ["chess_dev", "chess_prod"]),
    "10-verified-source":   (["bronze_github_subset"], ["github_subset"]),
    "11-state":             (["bronze_github_etag"], ["github_etag"]),
    "12-load-packages":     (["bronze_chess"], ["chess_bronze"]),
    "13-naming":            (["naming_snake", "naming_direct"],
                              ["naming_snake_case", "naming_direct"]),
    "14-merge-keys":        (["mk_pk", "mk_mk", "mk_dedup"],
                              ["pk_only", "merge_key", "pk_dedup_sort"]),
    "15-destination-caps":  (["bronze_products"], ["products_bronze"]),
    "16-config-secrets":    (["bronze_github_a", "bronze_github_b"],
                              ["github_github_a", "github_github_b"]),
    "20-drift-timeline":    (["drift_permissive", "drift_strict", "drift_hybrid"],
                              ["drift_permissive", "drift_strict", "drift_hybrid"]),
    "21-retries":           (["resilience"], ["retries"]),
    "22-partial-failure":   (["resume_demo"], ["resume_demo"]),
    "23-streaming":         (["stream_naive", "stream_smart"],
                              ["mem_stream_naive", "mem_stream_smart"]),
    "24-data-quality":      (["bronze_dq"], ["dq"]),
    "25-unit-tests":        ([], []),
    "26-schema-tests":      (["schema_test_chess", "schema_freeze_demo"],
                              ["schema_tests", "schema_freeze_demo"]),
    "27-business-checks":   (["business_checks"], ["business_checks"]),
    "28-modelling":         (["customers_replace", "customers_scd2", "customers_json"],
                              ["cust_replace", "cust_scd2", "cust_json"]),
    "29-documentation":     (["docs_demo"], ["docs_demo"]),
    "30-evolving-pipeline": (["evolve_demo"], ["evolve_demo"]),
}


def expand(args: list[str]) -> list[str]:
    """Expand 'all', ranges (20-29), or numeric prefixes (01) into ex dir names."""
    out: list[str] = []
    for a in args:
        if a == "all" or a == "":
            return list(OWNED.keys())
        if "-" in a and a[0].isdigit() and a.split("-", 1)[1].isdigit():
            lo, hi = a.split("-", 1)
            lo_i, hi_i = int(lo), int(hi)
            for name in OWNED:
                n = int(name.split("-", 1)[0])
                if lo_i <= n <= hi_i:
                    out.append(name)
        else:
            # numeric prefix match (e.g. "01" → "01-pipeline")
            matches = [n for n in OWNED if n.startswith(a + "-") or n == a]
            if not matches:
                print(f"!! no exercise matches '{a}'", file=sys.stderr)
            out.extend(matches)
    return out


def drop_schema(ds: str) -> None:
    import duckdb
    if not WAREHOUSE.exists():
        return
    try:
        duckdb.connect(str(WAREHOUSE)).execute(f"DROP SCHEMA IF EXISTS {ds} CASCADE")
        print(f"  dropped schema  {ds}")
    except Exception as e:
        print(f"  ! failed to drop {ds}: {e}", file=sys.stderr)


def drop_pipeline_dir(name: str) -> None:
    p = DLT_HOME / name
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
        print(f"  removed pipeline dir  ~/.dlt/pipelines/{name}")


def nuke_everything() -> None:
    """Hard reset — drop the warehouse file and clear ALL pipeline dirs."""
    for p in WAREHOUSE.parent.glob("warehouse.duckdb*"):
        p.unlink()
        print(f"  removed {p.name}")
    if DLT_HOME.exists():
        for child in DLT_HOME.iterdir():
            shutil.rmtree(child, ignore_errors=True)
            print(f"  removed ~/.dlt/pipelines/{child.name}")


def reset_one(name: str) -> None:
    datasets, pipelines = OWNED.get(name, ([], []))
    print(f"\n== {name} ==")
    if not datasets and not pipelines:
        print("  (nothing to reset)")
        return
    for ds in datasets:
        drop_schema(ds)
    for pn in pipelines:
        drop_pipeline_dir(pn)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*",
                        help="exercise number(s), range (20-29), or 'all'")
    parser.add_argument("--list", action="store_true",
                        help="show what each exercise owns and exit")
    args = parser.parse_args()

    if args.list:
        for name, (ds, pn) in OWNED.items():
            print(f"{name}:")
            print(f"  datasets:  {ds or '—'}")
            print(f"  pipelines: {pn or '—'}")
        return 0

    if not args.targets:
        print("Hard reset — removing warehouse and ALL pipeline dirs.\n"
              "Press Ctrl+C in 3 seconds to abort.")
        import time
        try:
            time.sleep(3)
        except KeyboardInterrupt:
            print("aborted")
            return 1
        nuke_everything()
        return 0

    names = expand(args.targets)
    for n in names:
        reset_one(n)
    print("\ndone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
