"""Evidence-only Enna monetization readiness, never automatic sales.

Use private Supabase operational state. A named affiliate program is not proof
the owner's account is accepted, and provider commission is not bank receipt.
"""
import json
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from agent import Database

VN=ZoneInfo("Asia/Ho_Chi_Minh")
TRACKS={"affiliate_work_gear","brand_partnerships","office_digital_goods"}


def summarize(tracks, programs, proposals, receipts, *, now=None):
    now=now or datetime.now(timezone.utc)
    if not all(isinstance(rows,list) for rows in (tracks,programs,proposals,receipts)):
        raise ValueError("Incomplete monetization source")
    active_programs=sum(
        r.get("review_status")=="active" for r in programs if isinstance(r,dict)
    )
    pending_proposals=sum(
        r.get("review_status")=="pending" for r in proposals if isinstance(r,dict)
    )
    active=[]; unready=[]
    for row in tracks:
        if not isinstance(row,dict) or row.get("track_key") not in TRACKS:
            continue
        ready=all(row.get(k) is True for k in
                  ("owner_approved","fulfillment_verified",
                   "claims_verified","disclosures_ready"))
        if row.get("stage")=="live" and ready:
            active.append(row["track_key"])
        else:
            unready.append(row["track_key"])
    # Only confirmed-receipt rows with nonempty evidence references count.
    received=0
    counted=0
    for row in receipts:
        if not isinstance(row,dict): continue
        amount=row.get("amount_received_vnd")
        if (type(amount) is int and amount>0 and
                row.get("verification_method") in
                ("owner_bank_reconciliation","provider_settlement_export") and
                isinstance(row.get("evidence_reference"),str) and
                len(row["evidence_reference"].strip())>=12):
            received+=amount
            counted+=1

    actions=[]
    if not active_programs:
        actions.append("check_koc_publisher_approval")
    if pending_proposals:
        actions.append("review_existing_affiliate_draft")
    if "office_digital_goods" in unready:
        actions.append("validate_free_office_toolkit_demand")
    if "brand_partnerships" in unready:
        actions.append("prepare_evidence_based_media_kit")
    if not active:
        actions.append("keep_commercial_posts_unpublished")
    return {
        "phase":"measuring" if active else "pre_revenue",
        "tracks_total":len({x.get("track_key") for x in tracks if isinstance(x,dict) and x.get("track_key") in TRACKS}),
        "tracks_live":len(active),
        "owner_approved_active_programs":active_programs,
        "affiliate_proposals_pending":pending_proposals,
        "confirmed_receipt_count":counted,
        "received_vnd":received,
        "actions":actions,
        "as_of":now.astimezone(VN).isoformat(timespec="minutes"),
    }


def run(db=None, *, now=None):
    db=db or Database()
    queries={
      "tracks":("/enna_monetization_tracks",
                "track_key,stage,owner_approved,fulfillment_verified,claims_verified,disclosures_ready"),
      "programs":("/affiliate_programs","code,review_status"),
      "proposals":("/affiliate_opportunities","review_status,publishing_status"),
      "receipts":("/enna_revenue_receipts",
                  "amount_received_vnd,verification_method,evidence_reference"),
    }
    responses={}
    for name,(route,cols) in queries.items():
        rows=db.request("GET",route,params={"select":cols,"limit":"200"})
        if not isinstance(rows,list):
            raise ValueError("Monetization data source malformed")
        responses[name]=rows
    return summarize(responses["tracks"],responses["programs"],
                     responses["proposals"],responses["receipts"],now=now)


if __name__=="__main__":
    try:
        result=run()
        print("Enna monetization:",json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        # Do not expose raw HTTP exception: request may include credentials.
        print("Enna monetization:",json.dumps({
            "phase":"source_unavailable","error_class":type(exc).__name__
        }))
        sys.exit(1)
