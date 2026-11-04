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
        and any(x in s for x in (
            "nghi ben", "qua ben", "doi viec", "chuyen viec",
            "chuyen cho lam", "chuyen noi lam", "ung tuyen", "xin lam"
        ))
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
        "cong viec quan trong hon", "dong luc lam viec",
        "tinh toan", "loi nhuan", "diem cong", "chu dong tai chinh",
        "co ve", "chac dang", "chac se", "chac em", "chac ban",
        "kinh te gia dinh", "tiet kiem chi phi"
    )):
        return False
    mentions_perk=any(x in r for x in (
        "ma giam gia", "voucher", "coupon", "code", "ma uu dai",
        "uu dai", "giam gia", "khuyen mai", "quyen loi an"
    ))
    # A comment about changing shifts or imagining future coupon plans is
    # NOT the same as the author's punchline: changing employers.
    mentions_job_switch=any(x in r for x in (
        "nhay viec", "chuyen cho lam", "chuyen noi lam", "doi cho lam",
        "doi quan", "chuyen quan", "chuyen viec", "doi viec",
        "cap nhat cv", "nop cv", "cv moi", "nghi viec",
        "tuyen dung", "ung tuyen", "phuc loi", "noi lam tiep",
        "di lam cho khac", "chuyen cho", "chuyen ben"
    ))
    if any(x in r for x in (
        "doi ca", "ca lam moi", "ke hoach nhan them uu dai",
        "co ke hoach", "nhan them uu dai"
    )):
        return False
    return mentions_perk and mentions_job_switch


def tightly_grounded_fallbacks(source):
    """Small, factual backstops for unambiguous story twists only.

    Do not use for sensitive topics or generic social posts. These strings
    are *candidates* and still pass the standard brand/safety + independent
    model review before appearing anywhere. Not a publication authorization.
    """
    if is_coupon_job_change_story(source):
        return [
            "Hết mã giảm giá là em cập nhật CV luôn, lịch nhảy việc chạy theo voucher mất rồi =)))",
            "Đi làm theo hạn sử dụng mã giảm giá: hết ưu đãi là đến kỳ chuyển chỗ =)))",
            "Em này chuyển chỗ làm nhanh hơn vòng đời mã giảm giá, bộ phận tuyển dụng chắc bất ngờ =)))",
        ]
    return []
