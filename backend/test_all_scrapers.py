"""Run every registered scraper and report real results."""
import sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scrapers import SCRAPER_REGISTRY, get_scraper_class
from services.scraper_service import run_scraper

results = {}

for source_key, config in sorted(SCRAPER_REGISTRY.items()):
    print(f"  {source_key}... ", end="", flush=True)
    t0 = time.time()
    items, error = run_scraper(source_key)
    elapsed = time.time() - t0

    if error:
        print(f"X [{elapsed:.0f}s] FAIL: {error[:150]}")
        results[source_key] = ("FAIL", error[:150], 0, elapsed)
    elif not items:
        print(f"- [{elapsed:.0f}s] EMPTY")
        results[source_key] = ("EMPTY", "", 0, elapsed)
    else:
        sample = items[0].get("title","")[:80]
        has_date = bool(items[0].get("date"))
        has_url = bool(items[0].get("url") or items[0].get("link"))
        print(f"+ [{elapsed:.0f}s] {len(items):3d} items  title=\"{sample}\"  date={has_date}  url={has_url}")
        results[source_key] = ("OK", "", len(items), elapsed)

print(f"\n{'='*60}")
oks = sum(1 for v in results.values() if v[0]=="OK")
emps = sum(1 for v in results.values() if v[0]=="EMPTY")
fails = sum(1 for v in results.values() if v[0]=="FAIL")
print(f"  {oks} OK  {emps} EMPTY  {fails} FAIL  ({len(results)} total)")
print(f"{'='*60}\n")

for k in sorted(results.keys()):
    s, d, n, e = results[k]
    icon = {"OK":"+","EMPTY":"-","FAIL":"X"}[s]
    extra = f" ({d})" if d else ""
    print(f"  {icon} {k:25s} [{s:5s}] {n:3d} items  {e:5.1f}s{extra}")
