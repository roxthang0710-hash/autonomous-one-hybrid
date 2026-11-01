"""Idempotently evaluate older research proposals (no external actions)."""
from agent import Database
from evaluator import evaluate_proposal


def backfill(db):
    proposals = db.request("GET", "/agent_proposals", params={
        "select": "id,proposal,research_sources", "order": "created_at.asc",
        "limit": "200",
    })
    done = {
        row["proposal_id"] for row in db.request(
            "GET", "/agent_evaluations",
            params={"select": "proposal_id", "limit": "200"},
        )
    }
    titles = []
    created = 0
    for row in proposals:
        proposal = row.get("proposal") or {}
        if row["id"] not in done:
            evaluation = evaluate_proposal(
                proposal, row.get("research_sources") or [], titles
            )
            db.insert("agent_evaluations", {
                "proposal_id": row["id"], **evaluation,
            })
            created += 1
        titles.append(proposal.get("title", ""))
    return created


if __name__ == "__main__":
    print("Historical evaluations added:", backfill(Database()))
