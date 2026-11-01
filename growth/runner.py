"""Automated growth radar (research only).

Public RSS -> safety/fit ranking -> one Groq idea in Supabase.
Official Threads keyword search works only after explicit Meta OAuth opt-in.
No seeding bots, fake identities, auto-replies, likes or spam publishing.
"""
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

from agent import Database
from growth.conversations import search_threads, QUERIES
from growth.generator import compose
from growth.scoring import classify
from growth.sources import discover

MAX_SOURCE_ROWS = 14
MAX_SHORTLIST = 5
MAX_DRAFTS_WEEK = 5


def key_for(now, run_id=""):
    if run_id and run_id.isdecimal() and 5 <= len(run_id) <= 20:
        return "github:" + run_id
    # Idempotent per 12-hour window for manual local runs.
    return "radar:" + now.strftime("%Y%m%d") + ":" + str(now.hour // 12)


def fingerprint(source, title):
    return hashlib.sha256((source + "\n" + title.casefold().strip()).encode()).hexdigest()


def build_candidates(feed_rows, threads_rows=(), now=None):
    now = now or datetime.now(timezone.utc)
    result, seen = [], set()
    for row in feed_rows:
        judgement = classify(row["title"], row.get("published_at"), now)
        if judgement["state"] != "candidate":
            continue
        record = {
            "fingerprint": row["fingerprint"], "source": row["source"],
            "title": row["title"], "source_url": row["source_url"],
            "published_at": row.get("published_at").isoformat()
                            if row.get("published_at") else None,
            "relevance_score": judgement["score"], "state": "candidate",
            "niche": judgement["niche"], "risk_flags": [],
            "notes": judgement["notes"],
        }
        if record["fingerprint"] not in seen:
            seen.add(record["fingerprint"])
            result.append(record)

    for row in threads_rows:
        judgement = classify(row["title"], now=now)
        if judgement["state"] != "candidate":
            continue
        record = {
            "fingerprint": fingerprint("threads_keyword_api", row["id"]),
            "source": "threads_keyword_api",
            "title": row["title"], "source_url": row["url"],
            "source_post_id": row["id"],
            "source_username": row["username"],
            "published_at": None,
            "relevance_score": judgement["score"],
            "state": "candidate", "niche": judgement["niche"],
            "risk_flags": [], "notes": judgement["notes"],
        }
        if record["fingerprint"] not in seen:
            seen.add(record["fingerprint"])
            result.append(record)

    return sorted(result, key=lambda x: x["relevance_score"], reverse=True)[:MAX_SOURCE_ROWS]


def choose_for_draft(candidates, existing_fingerprints):
    for row in candidates:
        if row["fingerprint"] not in existing_fingerprints:
            return row
    return None


def run(db=None, now=None):
    db = db or Database()
    now = now or datetime.now(timezone.utc)
    run_key = key_for(now, os.getenv("GITHUB_RUN_ID", ""))
    existing = db.request("POST", "/growth_runs",
        params={"on_conflict": "run_key"},
        payload={"run_key": run_key},
        prefer="resolution=ignore-duplicates,return=representation")
    if not existing:
        return "already_processed"
    run_row = existing[0]
    run_id = run_row["id"]
    try:
        # Prevent runaway Groq usage and unreviewed drafts.
        week = now - timedelta(days=7)
        recent = db.request("GET", "/growth_opportunities", params={
            "select": "id", "created_at": "gte." + week.isoformat(),
            "limit": str(MAX_DRAFTS_WEEK),
        })
        if len(recent) >= MAX_DRAFTS_WEEK:
            db.patch("growth_runs", run_id, {
                "status": "no_relevant_signals",
                "source_summary": {"cap": "five_drafts_per_rolling_week"},
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            return "weekly_cap"

        public_rows, sources = discover()
        threads_rows = []
        threads_status = "not_authorized"
        if os.getenv("THREADS_DISCOVERY_ENABLED", "").lower() == "true":
            try:
                threads_rows, threads_status = search_threads(query=QUERIES[now.day % len(QUERIES)])
            except Exception:
                threads_status = "source_unavailable"
        selected = build_candidates(public_rows, threads_rows, now=now)

        if not public_rows and not threads_rows:
            outcome = "source_unavailable"
        elif not selected:
            outcome = "no_relevant_signals"
        else:
            outcome = "success"

        saved = []
        for row in selected[:MAX_SHORTLIST]:
            inserted = db.request("POST", "/growth_signals",
                params={"on_conflict": "fingerprint"}, payload=row,
                prefer="resolution=ignore-duplicates,return=representation")
            saved.extend(inserted)
        found = {x["fingerprint"]: x["id"] for x in saved}
        # Resolve IDs of newly inserted or previously stored signals.
        stored = db.request("GET", "/growth_signals", params={
            "select": "id,fingerprint",
            "fingerprint": "in.(" + ",".join(x["fingerprint"] for x in selected) + ")",
            "limit": str(MAX_SOURCE_ROWS),
        }) if selected else []
        found.update({x["fingerprint"]: x["id"] for x in stored})
        existing_ideas = db.request("GET", "/growth_opportunities", params={
            "select": "signal_id", "limit": "200",
            "order": "created_at.desc",
        })
        used_ids = {x["signal_id"] for x in existing_ideas}
        fresh = next((x for x in selected if x["fingerprint"] in found
                      and found[x["fingerprint"]] not in used_ids), None)
        drafts = 0
        if fresh:
            kind = "reply_suggestion" if fresh["source"] == "threads_keyword_api" else "trend_post"
            draft = compose(fresh, kind=kind)
            draft_text = draft["post_text"]
            quality = min(100, fresh["relevance_score"] + (
                5 if draft["verification_needed"] else 0))
            row = {
                "signal_id": found[fresh["fingerprint"]],
                "kind": kind, "status": "needs_review",
                "draft_text": draft_text,
                "hook": draft["hook"][:250],
                "relevance_reason": draft["relevance_reason"][:700],
                "why_safe": draft["why_safe"][:700],
                "quality_score": quality,
                "target_post_url": fresh.get("source_url") if kind == "reply_suggestion" else None,
                "target_post_id": fresh.get("source_post_id") if kind == "reply_suggestion" else None,
                "expires_at": (now + timedelta(hours=72)).isoformat(),
            }
            created = db.request("POST", "/growth_opportunities",
                params={"on_conflict": "signal_id,kind"}, payload=row,
                prefer="resolution=ignore-duplicates,return=representation")
            drafts = len(created)

        db.patch("growth_runs", run_id, {
            "status": outcome, "signal_count": len(public_rows) + len(threads_rows),
            "shortlisted": len(selected), "drafts_created": drafts,
            "source_summary": {
                "rss_sources": sources, "threads": threads_status,
                "original_drafts_only": True,
            },
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"status": outcome, "signals": len(public_rows) + len(threads_rows),
                "shortlisted": len(selected), "drafts": drafts,
                "threads_discovery": threads_status}
    except Exception as exc:
        db.patch("growth_runs", run_id, {
            "status": "failed", "error_kind": type(exc).__name__[:80],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        raise


if __name__ == "__main__":
    # Never log public source headlines, tokens or unpublished content to a public repo.
    print("Growth radar:", json.dumps(run(), ensure_ascii=False))
