"""Unattended editor + publisher after owner OAuth; graceful independent stages."""
import json
import os

from agent import Database
from threads.content import plan_next, seed_calendar, status
from threads.publisher import publish_due
from threads.insights import collect


def daily(db=None, *, publish=True, metrics=True):
    """A failed Groq generation must not disable a previously approved post."""
    db = db or Database()
    results = {}
    try:
        results["seed_existing"] = seed_calendar(db)
        results["editor"] = plan_next(
            db, force=os.getenv("THREADS_FORCE_GENERATION", "") == "true")
    except Exception as exc:
        # Do not print source text or secrets to public GitHub Actions.
        results["editor"] = "error:" + type(exc).__name__
    if publish:
        try:
            results["publisher"] = publish_due(db)
        except Exception as exc:
            results["publisher"] = "stopped:" + type(exc).__name__
    else:
        results["publisher"] = "disabled_for_manual_planning"
    if metrics:
        try:
            results["insights"] = collect(db)
        except Exception as exc:
            results["insights"] = "unavailable:" + type(exc).__name__
    try:
        results["queue"] = status(db)["posts"]
    except Exception:
        results["queue"] = "unavailable"
    return results


if __name__ == "__main__":
    print(json.dumps(daily(), ensure_ascii=False))
