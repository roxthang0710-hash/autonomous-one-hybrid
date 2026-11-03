"""Read-only, evidence-first affiliate product shortlist for Enna.

Score = editorial RESEARCH priority, never SKU quality, ROI, or seller trust.
Outputs safe labels and counts; never prints private product/affiliate URLs.
"""
import json
from agent import Database

def prioritize(candidates, programs, experiments):
    if not all(isinstance(v,list) for v in (candidates,programs,experiments)):
        raise ValueError("Incomplete private Affiliate evidence")
    live_programs={p.get("code") for p in programs if p.get("review_status")=="active"}
    scores=sorted(
        [p for p in candidates if isinstance(p,dict) and
         p.get("stage") not in ("retired",) and
         type(p.get("internal_priority_score")) is int],
        key=lambda r:(-r["internal_priority_score"],r.get("candidate_key",""))
    )
    top=[]
    for row in scores[:4]:
        verified=all(row.get(k) is True for k in (
            "publisher_approved","seller_verified","product_verified",
            "disclosure_ready","owner_approved"))
        ready=(verified and row.get("stage") in ("approved","published")
               and bool(row.get("affiliate_url")) and
               row.get("program_code") in live_programs)
        blockers=[]
        if row.get("program_code") not in live_programs:blockers.append("publisher_not_confirmed")
        if not row.get("seller_verified"):blockers.append("seller_not_verified")
        if not row.get("product_verified"):blockers.append("sku_not_verified")
        if not row.get("owner_approved"):blockers.append("owner_review_missing")
        if not row.get("disclosure_ready"):blockers.append("commercial_disclosure_missing")
        top.append({"category_key":row.get("candidate_key"),
                    "editorial_priority":row["internal_priority_score"],
                    "cleared_for_affiliate":ready,"blockers":blockers})
    return {
        "hypothesis_count":len(scores),
        "cleared_product_count":sum(
          p.get("cleared_for_affiliate",False) for p in
          [
            {"cleared_for_affiliate":(
              all(x.get(k) is True for k in
                  ("publisher_approved","seller_verified","product_verified",
                   "disclosure_ready","owner_approved"))
              and x.get("stage") in ("approved","published")
              and bool(x.get("affiliate_url"))
              and x.get("program_code") in live_programs)}
            for x in scores
          ]),
        "placement_plan_count":sum(x.get("status")=="planned" for x in experiments if isinstance(x,dict)),
        "active_placement_count":sum(x.get("status")=="active" for x in experiments if isinstance(x,dict)),
        "top_research":top,
        "publication_allowed":bool(live_programs) and any(x["cleared_for_affiliate"] for x in top),
        "next_step":"validate_publisher_then_test_sku" if not live_programs
                    else "validate_specific_sku",
    }

def run(db=None):
    db=db or Database()
    sources=[
        ("/enna_affiliate_candidates","candidate_key,program_code,stage,affiliate_url,owner_approved,publisher_approved,seller_verified,product_verified,disclosure_ready,internal_priority_score"),
        ("/affiliate_programs","code,review_status"),
        ("/enna_affiliate_tests","status")
    ]
    result=[]
    for route,cols in sources:
        rows=db.request("GET",route,params={"select":cols,"limit":"150"})
        if not isinstance(rows,list):
            raise ValueError("Affiliate evidence unavailable")
        result.append(rows)
    return prioritize(*result)

if __name__=="__main__":
    try:
        print("Enna product selection:",json.dumps(run(),ensure_ascii=False))
    except Exception as exc:
        print("Enna product selection unavailable:",type(exc).__name__)
        raise SystemExit(1)
