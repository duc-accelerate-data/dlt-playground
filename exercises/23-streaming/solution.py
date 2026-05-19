"""Reference solution for exercise 23."""
import sys, resource as rss
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import dlt

PAGES, PAGE_SIZE = 100, 1000
WH = REPO / "data" / "warehouse.duckdb"


def fake_page(p):
    return [{"i": p * PAGE_SIZE + j, "payload": "x" * 200} for j in range(PAGE_SIZE)]


@dlt.resource(name="rows", primary_key="i", write_disposition="merge")
def naive():
    buf = []
    for p in range(PAGES):
        buf.extend(fake_page(p))
    yield buf  # one giant yield — high memory


@dlt.resource(name="rows", primary_key="i", write_disposition="merge")
def stream():
    # Chunk tuning in dlt 1.x lives in normalize/extract config (BUFFER_MAX_ITEMS,
    # FILE_MAX_ITEMS) not as a resource kwarg. The lesson is the *yield shape*:
    # per-page generator yields are bounded; a single mega-list yield is not.
    for p in range(PAGES):
        yield fake_page(p)


def run_and_measure(res, dataset):
    p = dlt.pipeline(
        pipeline_name=f"mem_{dataset}",
        destination=dlt.destinations.duckdb(str(WH)),
        dataset_name=dataset,
    )
    p.run(res)
    peak_kb = rss.getrusage(rss.RUSAGE_SELF).ru_maxrss  # macOS bytes / linux kb
    return peak_kb


print(f"naive peak ru_maxrss  = {run_and_measure(naive(),  'stream_naive'):>12}")
print(f"stream peak ru_maxrss = {run_and_measure(stream(), 'stream_smart'):>12}")
print("(ru_maxrss is cumulative — the second value should be only marginally higher.")
print(" Restart Python between runs for a clean comparison.)")
