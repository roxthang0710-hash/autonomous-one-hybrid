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
MAX_DRAFTS_WEEK = 21  # up to three genuine opportunities/day; never a quota
MAX_EDITORIAL_DRAFTS_WEEK = 5
MAX_CONTENT_ATTEMPTS = 3  # Invalid AI text is rejected, not a job failure.


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
        judgement = classify(row["title"], row.get("published_at"), now)
        if judgement["state"] != "candidate":
            continue
        record = {
            "fingerprint": fingerprint("threads_keyword_api", row["id"]),
            "source": "threads_keyword_api",
            "title": row["title"], "source_url": row["url"],
            "source_post_id": row["id"],
            "source_username": row["username"],
            "published_at": row["published_at"].isoformat(),
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
                "source_summary": {"cap": "twenty_one_drafts_per_rolling_week"},
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            return "weekly_cap"

        public_rows, sources = discover()
        threads_rows = []
        threads_status = "not_authorized"
        if os.getenv("THREADS_DISCOVERY_ENABLED", "").lower() != "false":
            try:
                # Owner enabled Growth scopes in the secure Meta OAuth portal.
                vault = db.request("POST", "/rpc/threads_read_vault_token",
                                   payload={"p_brand_key": "do_hay_di_lam"})
                if vault and vault[0].get("enable_replies") is True:
                    from threads.credentials import load_credentials
                    auth = load_credentials(db, refresh=False)
                    if auth:
                        # Three daily searches rotate narrow, relevant
                        # topics. One midday query checks TOP; all results
                        # still must be less than 24 hours old.
                        slot = (now.hour // 5)
                        threads_rows, threads_status = search_threads(
                            query=QUERIES[(now.timetuple().tm_yday * 3 + slot) % len(QUERIES)],
                            token=auth[0],
                            search_type="TOP" if slot % 3 == 1 else "RECENT")
            except Exception:
                threads_status = "source_unavailable"
        selected = build_candidates(public_rows, threads_rows, now=now)

        if not public_rows and not threads_rows:
            outcome = "source_unavailable"
        elif not selected:
            outcome = "no_relevant_signals"
        else:
            outcome = "success"

        shortlisted = selected[:MAX_SHORTLIST]
        # Reserve one candidate slot for a genuine Threads discussion when
        # official search scope is available, rather than crowding it out with
        # broadly popular Google News headlines.
        one_thread = next(
            (x for x in selected if x["source"] == "threads_keyword_api"
             and x["relevance_score"] >= 65), None
        )
        if one_thread and one_thread not in shortlisted:
            shortlisted = shortlisted[:-1] + [one_thread]
        saved = []
        for row in shortlisted:
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
            "select": "signal_id,kind", "limit": "200",
            "order": "created_at.desc",
        })
        used_ids = {x["signal_id"] for x in existing_ideas}
        available = [x for x in shortlisted if x["fingerprint"] in found
                     and found[x["fingerprint"]] not in used_ids]
        # Editorial drafts remain capped while specific, genuinely useful
        # replies can reach a safe maximum of three in a day. These are
        # opportunities, not instructions to force three comments.
        weekly_editorial = sum(
            x.get("kind") == "trend_post" for x in existing_ideas
        )
        # Deduplicated per target; safety RPC imposes the actual daily limit
        # at publishing time.
        reply_history = sum(x.get("kind") == "reply_suggestion"
                            for x in existing_ideas[:15])
        first_thread = next((x for x in available
                             if x["source"] == "threads_keyword_api" and
                             x["relevance_score"] >= 60), None)
        # Prefer a real, fresh Threads conversation; do not turn brand
        # growth into 21 generic news-reaction drafts each week.
        fresh = first_thread or (
            next((x for x in available
                  if x["source"] != "threads_keyword_api"), None)
            if weekly_editorial < MAX_EDITORIAL_DRAFTS_WEEK else None)
        drafts = 0
        rejected_drafts = 0
        # A single Groq response can fail editorial safety checks. Reject
        # that result, try a different *verified source* (bounded), and keep
        # the entire scheduled research job healthy. Network, auth or DB
        # failures still surface so operators can notice real outages.
        if fresh:
            alternatives = [fresh] + [
                x for x in available
                if x["fingerprint"] != fresh["fingerprint"] and
                (x["source"] == "threads_keyword_api" or
                 weekly_editorial < MAX_EDITORIAL_DRAFTS_WEEK)
            ]
            for candidate in alternatives[:MAX_CONTENT_ATTEMPTS]:
                kind = ("reply_suggestion"
                        if candidate["source"] == "threads_keyword_api"
                        else "trend_post")
                try:
                    prior_rows = db.request("GET", "/growth_opportunities", params={
                        "select": "draft_text",
                        "order": "created_at.desc", "limit": "12",
                    })
                    prior_texts = [
                        r["draft_text"] for r in prior_rows
                        if isinstance(r.get("draft_text"), str)
                    ]
                    draft = compose(candidate, kind=kind, prior_texts=prior_texts)
                except ValueError:
                    # No unsafe text is saved to Supabase or printed in logs.
                    rejected_drafts += 1
                    continue
                quality = min(100, candidate["relevance_score"] + (
                    5 if draft["verification_needed"] else 0) +
                    (10 if kind == "reply_suggestion" else 0))
                row = {
                    "signal_id": found[candidate["fingerprint"]],
                    "kind": kind, "status": "needs_review",
                    "draft_text": draft["post_text"],
                    "hook": draft["hook"][:250],
                    "relevance_reason": draft["relevance_reason"][:700],
                    "why_safe": draft["why_safe"][:700],
                    "quality_score": quality,
                    "target_post_url": (candidate.get("source_url")
                                        if kind == "reply_suggestion" else None),
                    "target_post_id": (candidate.get("source_post_id")
                                       if kind == "reply_suggestion" else None),
                    "expires_at": (now + timedelta(hours=72)).isoformat(),
                }
                created = db.request("POST", "/growth_opportunities",
                    params={"on_conflict": "signal_id,kind"}, payload=row,
                    prefer="resolution=ignore-duplicates,return=representation")
                drafts = len(created)
                # At most one draft per run, even if concurrent upsert inserted it.
                break

        db.patch("growth_runs", run_id, {
            "status": outcome, "signal_count": len(public_rows) + len(threads_rows),
            "shortlisted": len(selected), "drafts_created": drafts,
            "source_summary": {
                "rss_sources": sources, "threads": threads_status,
                "original_drafts_only": True,
                "rejected_unsafe_drafts": rejected_drafts,
            },
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"status": outcome, "signals": len(public_rows) + len(threads_rows),
                "shortlisted": len(selected), "drafts": drafts,
                "rejected_unsafe_drafts": rejected_drafts,
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
