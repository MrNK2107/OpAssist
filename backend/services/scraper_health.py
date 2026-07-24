import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ScraperRunStats:
    last_run: Optional[float] = None
    last_success: Optional[float] = None
    last_error: Optional[float] = None
    last_error_msg: str = ""
    total_runs: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_items: int = 0
    total_errors: int = 0
    last_items_found: int = 0
    last_duration: float = 0.0


class ScraperHealthTracker:
    def __init__(self):
        self._stats: dict[str, ScraperRunStats] = defaultdict(ScraperRunStats)
        self._source_status: dict[str, str] = {}

    def record_run(self, source_key: str, items_found: int, duration: float, error: Optional[str] = None):
        stats = self._stats[source_key]
        now = time.time()
        stats.last_run = now
        stats.total_runs += 1
        stats.last_items_found = items_found
        stats.last_duration = duration
        stats.total_items += items_found

        if error:
            stats.last_error = now
            stats.last_error_msg = error
            stats.total_failures += 1
        else:
            stats.last_success = now
            stats.total_successes += 1
            stats.total_errors += 0

    def record_upsert_errors(self, source_key: str, errors: int):
        if errors > 0:
            self._stats[source_key].total_errors += errors

    def set_source_status(self, source_key: str, status: str):
        self._source_status[source_key] = status

    def get_stats(self, source_key: str) -> ScraperRunStats:
        return self._stats[source_key]

    def get_all_stats(self) -> dict:
        result = {}
        for key, stats in self._stats.items():
            result[key] = {
                "last_run": stats.last_run,
                "last_success": stats.last_success,
                "last_error": stats.last_error,
                "last_error_msg": stats.last_error_msg,
                "total_runs": stats.total_runs,
                "total_successes": stats.total_successes,
                "total_failures": stats.total_failures,
                "total_items": stats.total_items,
                "total_errors": stats.total_errors,
                "last_items_found": stats.last_items_found,
                "last_duration": stats.last_duration,
                "success_rate": round(
                    (stats.total_successes / stats.total_runs * 100) if stats.total_runs > 0 else 0, 1
                ),
            }
        return result

    def summary(self) -> dict:
        stats = self.get_all_stats()
        total_items = sum(s["total_items"] for s in stats.values())
        total_runs = sum(s["total_runs"] for s in stats.values())
        total_failures = sum(s["total_failures"] for s in stats.values())
        active = sum(1 for s in self._source_status.values() if s == "active")
        unstable = sum(1 for s in self._source_status.values() if s == "unstable")
        broken = sum(1 for s in self._source_status.values() if s == "broken")

        return {
            "total_sources": len(stats),
            "active_sources": active,
            "unstable_sources": unstable,
            "broken_sources": broken,
            "total_runs": total_runs,
            "total_failures": total_failures,
            "total_items_collected": total_items,
            "overall_success_rate": round(
                ((total_runs - total_failures) / total_runs * 100) if total_runs > 0 else 0, 1
            ),
        }


health_tracker = ScraperHealthTracker()
