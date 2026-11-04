"""Enna autonomous editorial recovery loop for owner-selected Threads Issues.

Monitors existing user-submitted Github Issues. Diagnoses failed AI drafting,
retries with diverse prompts and model fallback, and saves one compact
self-healing status comment. NEVER contacts Meta/Threads or triggers posting.
Requires no owner re-selection and no manual /enna draft command.
"""
from __future__ import annotations
import datetime as dt
import os
import re
import requests
from growth.companion_editor import compose_selected_options, compose_selected
from growth.companion_judge import judge_selected
from growth.companion_selected_reply import (
    can_send, clean_selected_excerpt, decode_issue_body,
)

MARKER = "<!-- ENNA_SELFHEAL_V1"
MAX_ATTEMPTS = 3
WINDOW_HOURS = 72
MIN_INTERVAL_MINUTES = 45
HARD_STOP = ("✅ Enna đã nhận xác nhận phản hồi từ Meta.",
             "⚠️ Meta không trả về kết quả chắc chắn.",
             "Meta từ chối tạo bình luận",
             "Không tự thử lại")
DRAFT_DONE = ("🧪 KIỂM THỬ NỘI DUNG", "Enna đã soạn bình luận nhưng Meta")
FAILURE_WORDS = ("không bám đủ sát", "không thấy bình luận bám đủ sát",
                 "bản nháp AI không đạt",
                 "dịch vụ tạo nội dung chưa phản hồi", "no_safe_draft",
                 "chưa tạo được bản nháp", "chưa phản hồi thành công",
                 "không có cách bình luận", "ai_reply_not_contextual_enough",
                 "không thấy cách bình luận",
                 "bộ kiểm thử biên tập chưa đạt")


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def parse_time(value):
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def state_marker(comments):
    for c in reversed(comments):
        body=str(c.get("body") or "")
        if MARKER not in body:
            continue
        match=re.search(r"<!-- ENNA_SELFHEAL_V1 attempts=(\d+) last=([0-9TZ:+-]+) status=([a-z_]+) -->",body)
        if match:
            return {"id":int(c["id"]), "attempts":int(match.group(1)),
                    "last":parse_time(match.group(2)), "status":match.group(3)}
    return {"id":None,"attempts":0,"last":None,"status":"new"}


def eligible(issue, comments, *, owner, now=None):
    now=now or utcnow()
    if not issue or issue.get("pull_request"):
        return False
    if (issue.get("user") or {}).get("login")!=owner:
        return False
    if not str(issue.get("title") or "").startswith("enna-pick:"):
        return False
    when=parse_time(issue.get("created_at"))
    if not when or not dt.timedelta(0)<=now-when<=dt.timedelta(hours=WINDOW_HOURS):
        return False
    progress=state_marker(comments)
    if progress["status"]=="repaired" or progress["attempts"]>=MAX_ATTEMPTS:
        return False
    if (progress["last"] and
        now-progress["last"]<dt.timedelta(minutes=MIN_INTERVAL_MINUTES)):
        return False
    # Look only at normal bot results; self-heal's own status is not a
    # diagnostic of Meta status. A definitive/uncertain write is a hard stop.
    previous=[
        str(c.get("body") or "") for c in comments
        if (c.get("user") or {}).get("login")=="github-actions[bot]"
        and MARKER not in str(c.get("body") or "")
    ]
    if not previous:
        return False
    if any(any(stop in message for stop in HARD_STOP) for message in previous):
        return False
    if any(any(success in message for success in DRAFT_DONE) for message in previous):
        # A valid draft has already been provided. Self-heal is about
        # editorial failures, not automatically posting old candidates.
        return False
    latest=previous[-1]
    return any(term in latest for term in FAILURE_WORDS)


def make_recovery_draft(issue, *, propose=compose_selected_options,
                        writer=compose_selected, reviewer=judge_selected):
    """Create a short approved draft; NEVER any Threads write operation."""
    target, selected, verdict=decode_issue_body(issue["body"])
    selected=clean_selected_excerpt(selected,author=target["username"])
    if not 35<=len(selected)<=1800:
        return None
    # This is a source emphasis, not a reason to copy original text.
    from growth.companion_editor import important_source_clauses
    last=important_source_clauses(selected)
    last_detail=last[-1] if last else selected[-140:]
    feedback=(
        "TỰ SỬA bản trước. Chỉ một câu 60-120 ký tự. "
        "Chú ý đúng CÂU CHỐT của chuyện: "+last_detail[:160]+". "
        "Đáp tự nhiên, không nói chung chung về đạo đức công việc, "
        "không nhắc lại bài, không tâng bốc, không gồng, không bịa "
        "chi tiết khác. Nếu không có câu hay, chọn không bình luận."
    )
    prior=[]
    saved_model=os.environ.get("GROQ_MODEL")
    try:
        # Bounded fallback to a different deployed model when provider
        # JSON formatting/reasoning fails. No retry loops without limits.
        for model in ("openai/gpt-oss-120b","openai/gpt-oss-20b"):
            os.environ["GROQ_MODEL"]=model
            try:
                options=propose({
                    "title":selected, "niche":verdict["niche"],
                    "source_url":target["url"]},
                    earlier=tuple(prior))
            except (requests.RequestException,ValueError,KeyError,TypeError):
                options=[]
            for option in options[:3]:
                if not isinstance(option,dict):
                    continue
                candidate=str(option.get("post_text") or "").strip()
                if candidate:
                    prior.append(candidate)
                if (candidate and
                    can_send(candidate,selected,target=target,semantic_override=True)
                    and reviewer(selected,candidate)):
                    return {"draft":candidate, "model":model,"target":target["url"]}
            try:
                candidate=writer({
                    "title":selected,"source_url":target["url"],
                    "niche":verdict["niche"],"quality_feedback":feedback},
                    kind="reply_suggestion", prior_texts=tuple(prior))
                proposed=str(candidate.get("post_text") or "").strip()
                if (candidate.get("should_reply") and
                    can_send(proposed,selected,target=target,semantic_override=True)
                    and reviewer(selected,proposed)):
                    return {"draft":proposed,"model":model,"target":target["url"]}
            except (requests.RequestException,ValueError,KeyError,TypeError):
                pass
    finally:
        if saved_model is None:
            os.environ.pop("GROQ_MODEL",None)
        else:
            os.environ["GROQ_MODEL"]=saved_model
    return None


class Github:
    def __init__(self, repo, token, *, client=requests):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+",repo):
            raise ValueError("invalid_repository")
        if not token:
            raise ValueError("missing_token")
        self.repo=repo
        self.client=client
        self.headers={
            "Authorization":"Bearer "+token,
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28",
        }
        self.base="https://api.github.com/repos/"+repo

    def request(self, method, path, **kwargs):
        response=self.client.request(
            method,self.base+path,headers=self.headers,timeout=20,**kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def issues(self):
        items=self.request("GET",
            "/issues?state=open&sort=created&direction=desc&per_page=15")
        return [i for i in items if not i.get("pull_request")]

    def comments(self, number):
        return self.request("GET",f"/issues/{int(number)}/comments?per_page=100")

    def status(self, number, previous, attempts, text, *, status, now=None):
        now=now or utcnow()
        stamp=now.isoformat(timespec="seconds").replace("+00:00","Z")
        marker=f"<!-- ENNA_SELFHEAL_V1 attempts={attempts} last={stamp} status={status} -->"
        body=marker+"\n"+text
        if previous["id"] is None:
            return self.request("POST",f"/issues/{int(number)}/comments",
                                json={"body":body})
        return self.request("PATCH",f"/issues/comments/{previous['id']}",
                            json={"body":body})


def run(*, github=None, recover=make_recovery_draft, now=None,
        manual_issue=None):
    now=now or utcnow()
    github=github or Github(os.environ["GITHUB_REPOSITORY"],
                            os.environ.get("GH_TOKEN",""))
    owner=github.repo.split("/",1)[0]
    # Handle one failed issue per invocation, keeping the provider/API budget
    # predictable. Schedule runs repeatedly without owner re-submission.
    for issue in github.issues():
        number=issue.get("number")
        if not number or (manual_issue and number!=manual_issue):
            continue
        comments=github.comments(number)
        if not eligible(issue,comments,owner=owner,now=now):
            continue
        progress=state_marker(comments)
        attempt=progress["attempts"]+1
        draft=None
        try:
            draft=recover(issue)
        except (requests.RequestException,ValueError,TypeError,KeyError):
            draft=None
        if draft:
            # IMPORTANT: not one of the Chrome extension's publishable markers.
            status="repaired"
            message=("🧰 Enna đã tự sửa lỗi biên tập và tạo được bình luận "
                     "ngắn, đúng ngữ cảnh. **CHỈ KIỂM THỬ — KHÔNG TỰ ĐĂNG THREADS.**"
                     "\n\nGợi ý đã kiểm tra:\n\n> "+draft["draft"]+
                     "\n\nTác vụ tự phục hồi đã hoàn tất, không yêu cầu "
                     "chủ tài khoản chọn lại bài.")
        else:
            status="retrying" if attempt<MAX_ATTEMPTS else "needs_attention"
            message=("🧰 Enna đang tự xử lý lỗi nội dung trong giới hạn "
                     "an toàn. **Không đăng bình luận khi chưa có bản phù hợp.** "
                     "Số lượt tự phục hồi: "+str(attempt)+"/"+str(MAX_ATTEMPTS)+
                     ("." if attempt<MAX_ATTEMPTS else
                      ". Đã đạt giới hạn, cần sửa mã/khóa API thay vì thử vô hạn."))
        github.status(number,progress,attempt,message,status=status,now=now)
        print("Enna self-heal:",number,status,"attempt",attempt)
        return {"issue":number,"status":status,"attempt":attempt}
    print("Enna self-heal: no eligible issue")
    return {"status":"no_eligible_issue"}


if __name__=="__main__":
    manual=os.getenv("ENNA_HEAL_ISSUE","").strip()
    run(manual_issue=int(manual) if manual.isdecimal() else None)
