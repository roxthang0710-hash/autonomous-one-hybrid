"""A1.2: persistent, evidence-checked incident lifecycle.

The engine maintains a private, service-only incident ledger. It cannot
publish social content or infer a resolved Metricool error from a cached row.
A stale-follower incident can resolve ONLY after a newer official Meta
snapshot, with verified timestamps. Other incidents stay blocked until
an independent provider check is implemented in A2.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from agent import Database
from growth.autonomy_controller import (
    BRAND, aware_time, fresh_official_snapshot, inspect_provider,
)

MAX_OBSERVED = 3
STALE_HORIZON = timedelta(hours=12)
FOLLOWER_KEY = "autonomy-v1:official_followers_stale"
TABLE = "/enna_autonomy_incidents"


def valid_prior(rows):
    if not isinstance(rows, list):
        raise RuntimeError("incident_ledger_unavailable")
    return {
        row["incident_key"]: row
        for row in rows if isinstance(row, dict)
        and isinstance(row.get("incident_key"), str)
        and row.get("brand_key") == BRAND
        and row.get("state") in {"open", "blocked", "resolved"}
    }


def active_candidates(followers, provider_rows, now):
    """Return a stable, bounded set of claims with evidence provenance."""
    provider_issues = inspect_provider(provider_rows, now)
    current_by_key = {}
    for row in provider_rows:
        if not isinstance(row, dict):
            continue
        key = (row.get("provider"), str(row.get("metricool_uuid") or ""))
        current_by_key[key] = row
    candidates = []
    for issue in provider_issues:
        key_parts = issue["key"].split(":")
        if len(key_parts) != 4:
            continue
        _, _, provider, uuid = key_parts
        evidence = current_by_key.get((provider, uuid))
        if not evidence:
            continue
        try:
            observed_at = aware_time(evidence["checked_at"])
        except (KeyError, ValueError, TypeError, OverflowError):
            continue
        # If the source claims to have been checked in the future, do NOT
        # overwrite incident evidence or re-open a formerly resolved case.
        if observed_at > now + timedelta(minutes=2):
            continue
        candidates.append({
            "incident_key": issue["key"],
            "incident_code": issue["code"],
            "provider": provider,
            "priority": issue["priority"],
            "state": "blocked",
            "source_kind": "supabase_snapshot",
            "evidence_at": observed_at.isoformat(),
            "reason_code": "needs_live_metricool_verification",
        })
    if fresh_official_snapshot(followers, now, max_age=STALE_HORIZON) is None:
        candidates.append({
            "incident_key": FOLLOWER_KEY,
            "incident_code": "official_followers_stale",
            "provider": None,
            "priority": 80,
            "state": "open",
            "source_kind": "meta_official",
            "evidence_at": None,
            "reason_code": "awaiting_fresh_official_meta_snapshot",
        })
    candidates.sort(key=lambda x: (-x["priority"], x["incident_key"]))
    # Do not hide the follower-recovery incident behind several old
    # publisher errors: it is the one issue we CAN verify autonomously.
    follower = next((x for x in candidates if x["incident_key"] == FOLLOWER_KEY), None)
    if follower and follower not in candidates[:MAX_OBSERVED]:
        return candidates[:MAX_OBSERVED - 1] + [follower]
    return candidates[:MAX_OBSERVED]


def plan_actions(candidates, prior, followers, now):
    """Pure transition planner, conservative when source state is uncertain."""
    existing = valid_prior(prior)
    actions = []
    active_keys = {x["incident_key"] for x in candidates}

    for issue in candidates:
        previous = existing.get(issue["incident_key"])
        if not previous:
            actions.append(("insert", issue["incident_key"], issue))
            continue
        if previous["state"] == "resolved":
            # A previously closed follower issue may recur 12h after the
            # latest official reading; this is a NEW episode.
            if issue["incident_key"] == FOLLOWER_KEY:
                try:
                    last_proof = aware_time(previous["resolution_evidence_at"])
                    if now - last_proof <= STALE_HORIZON:
                        continue
                except (KeyError, ValueError, TypeError, OverflowError):
                    continue
            else:
                # A cached Metricool ERROR observed before the LAST verified
                # provider resolution MUST NOT reopen the old case.
                observed = issue.get("evidence_at")
                resolved_evidence = previous.get("resolution_evidence_at")
                if not observed or not resolved_evidence:
                    continue
                try:
                    if aware_time(observed) <= aware_time(resolved_evidence):
                        continue
                except (TypeError, ValueError, OverflowError):
                    continue
            actions.append(("reopen", issue["incident_key"], issue))
            continue
        # Never regress a source evidence timestamp to an older version.
        try:
            if (previous.get("evidence_at") and issue.get("evidence_at")
                    and aware_time(issue["evidence_at"]) < aware_time(previous["evidence_at"])):
                continue
        except (TypeError, ValueError, OverflowError):
            continue
        actions.append(("observe", issue["incident_key"], issue))

    official = fresh_official_snapshot(followers, now)
    stale = existing.get(FOLLOWER_KEY)
    if (official and stale and stale["state"] != "resolved"
            and FOLLOWER_KEY not in active_keys):
        try:
            first_seen = aware_time(stale["first_seen_at"])
        except (TypeError, ValueError, KeyError, OverflowError):
            first_seen = None
        if first_seen and official["at"] >= first_seen - timedelta(seconds=2):
            actions.append(("resolve", FOLLOWER_KEY, {
                "state": "resolved",
                "resolved_at": now.isoformat(),
                "last_seen_at": now.isoformat(),
                "resolution_source": "meta_official",
                "resolution_evidence_at": official["at"].isoformat(),
                "reason_code": "verified_newer_meta_snapshot",
            }))

    # Provider issues are NEVER auto-resolved by disappearance from cached DB.
    return actions


def verified_write(db, method, key, payload, now):
    params = {"brand_key": "eq." + BRAND, "incident_key": "eq." + key}
    if method == "insert":
        value = {
            "brand_key": BRAND, **payload,
            "first_seen_at": now.isoformat(),
            "last_seen_at": now.isoformat(),
            "resolved_at": None,
        }
        saved = db.request("POST", TABLE,
            params={"on_conflict": "brand_key,incident_key"},
            payload=value,
            prefer="resolution=ignore-duplicates,return=representation")
    elif method in ("observe", "reopen", "resolve"):
        if method in ("observe", "reopen"):
            value = {**payload, "last_seen_at": now.isoformat(),
                     "resolved_at": None, "resolution_source": None,
                     "resolution_evidence_at": None}
            if method == "reopen":
                value["first_seen_at"] = now.isoformat()
                params["state"] = "eq.resolved"
        else:
            value = payload
            params["state"] = "in.(open,blocked)"
        saved = db.request("PATCH", TABLE, params=params,
                           payload=value, prefer="return=representation")
    else:
        raise ValueError("invalid_lifecycle_action")
    if not isinstance(saved, list):
        raise RuntimeError("incident_write_unavailable")
    return bool(saved)


def run(db=None, *, now=None):
    db = db or Database()
    now = aware_time(now or datetime.now(timezone.utc))
    followers = db.request("GET", "/enna_threads_account_snapshots", params={
        "select": "brand_key,followers,source,measured_at",
        "brand_key": "eq." + BRAND,
        "order": "measured_at.desc", "limit": "5",
    })
    provider_rows = db.request("GET", "/enna_multichannel_posts", params={
        "select": "provider,metricool_uuid,scheduled_at,checked_at,provider_status,has_media",
        "brand_key": "eq." + BRAND, "limit": "150",
        "order": "scheduled_at.asc",
    })
    previous = db.request("GET", TABLE, params={
        "select": "brand_key,incident_key,incident_code,state,first_seen_at,"
                  "evidence_at,resolution_evidence_at",
        "brand_key": "eq." + BRAND, "limit": "200",
    })
    if not isinstance(followers, list) or not isinstance(provider_rows, list):
        raise RuntimeError("incident_source_unavailable")
    candidates = active_candidates(followers, provider_rows, now)
    transitions = plan_actions(candidates, previous, followers, now)
    completed = []
    for action, key, payload in transitions:
        changed = verified_write(db, action, key, payload, now)
        if changed:
            completed.append((action, key))
    # Verify DB state AFTER writes. A successful REST request alone is not proof.
    checked = db.request("GET", TABLE, params={
        "select": "brand_key,incident_key,incident_code,state,first_seen_at,"
                  "resolved_at,resolution_source,resolution_evidence_at",
        "brand_key": "eq." + BRAND, "limit": "200",
    })
    if not isinstance(checked, list):
        raise RuntimeError("incident_readback_unavailable")
    by_key = valid_prior(checked)
    for action, key in completed:
        row = by_key.get(key)
        expected = "resolved" if action == "resolve" else (
            "open" if key == FOLLOWER_KEY else "blocked")
        if not row or row.get("state") != expected:
            raise RuntimeError("incident_readback_not_verified")
        if action == "resolve" and (
            row.get("resolution_source") != "meta_official" or
            not row.get("resolution_evidence_at")):
            raise RuntimeError("meta_resolution_evidence_missing")
    return {
        "status": "verified" if transitions else "unchanged",
        "active_candidates": len(candidates),
        "transitions_attempted": len(transitions),
        "transitions_verified": len(completed),
        "blocked_external": sum(x["state"] == "blocked" for x in by_key.values()),
        "resolved_from_verified_meta": sum(
            action == "resolve" for action, _ in completed),
        "live_metricool_checked": False,
        "social_writes": 0, "account_permissions_changed": False,
    }


if __name__ == "__main__":
    try:
        print("ENNA_LIFECYCLE_RESULT="+json.dumps(run(), ensure_ascii=False))
    except Exception as exc:
        print("ENNA_LIFECYCLE_RESULT="+json.dumps({
            "status": "unavailable", "error_class": type(exc).__name__,
            "social_writes": 0,
        }, ensure_ascii=False))
        raise SystemExit(1)
