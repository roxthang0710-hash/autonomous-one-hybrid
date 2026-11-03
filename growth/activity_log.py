"""Emit auditable, non-sensitive Enna workflow events.

This is reporting only: missing telemetry must not initiate or repeat a publish.
Codes and values are hard allowlisted, never log prompts, tokens or raw errors.
"""
import os
import sys
from agent import Database

KINDS={"publisher","editor","reconcile","insights","learning","growth","research","system","metricool"}
STATUSES={"started","success","skipped","failed","uncertain","pending"}
CODES={
    "ops_started", "ops_completed", "ops_failed",
    "publisher_started", "publisher_completed", "publisher_failed",
    "growth_started", "growth_completed", "growth_failed",
    "research_started", "research_completed", "research_failed",
    "insights_completed", "learning_completed", "monetization_checked",
    "editorial_checked", "community_checked", "media_checked",
    "community_reply_posted", "community_no_eligible", "community_scope_attention",
    "community_limited", "media_concept_prepared", "media_no_new",
    "workflow_skipped", "workflow_failed",
}

def emit(db, kind, status, code, *, run_id):
    if kind not in KINDS or status not in STATUSES or code not in CODES:
        raise ValueError("Activity event must use predefined safe codes")
    if not str(run_id).isdigit() or len(str(run_id)) > 24:
        raise ValueError("Workflow run ID required")
    event=os.environ.get("GITHUB_EVENT_NAME","unknown")
    event=event if event in {"schedule","issues","workflow_dispatch"} else "unknown"
    payload={
        "origin":"github", "kind":kind, "status":status,
        "code":code, "run_key":str(run_id), "trigger_kind":event,
        "dedup_key":"github:"+str(run_id)+":"+kind+":"+status+":"+code,
    }
    return db.request("POST","/enna_activity_events",
        params={"on_conflict":"dedup_key"},payload=payload,
        prefer="resolution=ignore-duplicates,return=representation")

def main():
    if len(sys.argv)!=4:
        raise SystemExit("Usage: python -m growth.activity_log kind status code")
    kind,status,code=sys.argv[1:]
    run_id=os.environ.get("GITHUB_RUN_ID","")
    try:
        rows=emit(Database(),kind,status,code,run_id=run_id)
        print("Enna activity:",kind,status,code,"stored" if rows else "already_recorded")
    except Exception as exc:
        # Observability must fail independently; no raw HTTP response or secret
        # is printed in public CI logs.
        print("Enna activity unavailable:",type(exc).__name__)

if __name__=="__main__":
    main()
