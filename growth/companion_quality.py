"""Source-grounded editorial checks independent from a model's self-rating.

These are narrow safeguards on clear factual punchlines. They do not choose
posts, infer account identity, call Meta, or authorize a publication.
"""
from growth.scoring import normalize


def is_coupon_job_change_story(source):
    """Detect a specific joke: a person changes jobs after exhausting perks."""
    s=normalize(source)
    return (
        "ma giam gia" in s
        and any(x in s for x in ("dung het", "het ma", "het code", "het voucher"))
        and any(x in s for x in ("nghi ben", "qua ben", "doi viec", "chuyen viec"))
    )


def punchline_grounded(source, reply):
    """Require the actual story twist, not a generic lecture or invented trait."""
    if not isinstance(source,str) or not isinstance(reply,str):
        return False
    if not is_coupon_job_change_story(source):
        return True
    r=normalize(reply)
    # A sentence about "working hard to pay off food costs" ignores the
    # stated reason for switching jobs and invents a work-ethic claim.
    if any(x in r for x in (
        "cham chi", "co gang lam", "lam viec nghiem tuc",
        "bu lai chi phi", "tinh toan chi phi", "gia tri cong viec",
        "cong viec quan trong hon", "dong luc lam viec"
    )):
        return False
    mentions_perk=any(x in r for x in (
        "ma giam gia", "voucher", "coupon", "code", "ma uu dai",
        "uu dai", "giam gia", "khuyen mai", "quyen loi an"
    ))
    plays_on_change=any(x in r for x in (
        "het", "can", "chuyen", "doi", "nhay", "nghi",
        "qua ben", "tuyen", "cv", "don", "noi lam",
        "di lam", "cong ty", "cho lam", "ca lam"
    ))
    return mentions_perk and plays_on_change
