"""Enna Companion: process a SINGLE Threads post explicitly selected by the owner.

Trusted trigger: a GitHub Issue opened by the repository owner. The issue body
contains an owner-selected public excerpt (base64url UTF-8) + exact Threads
post permalink. Never automate browsing or click Threads web controls.

Enna writes a genuinely useful, topical reply using the existing Groq
connection, then may publish ONCE with official Meta Threads API only after
the target is verified via official GET /{media_id}. If Meta cannot read the
target, it returns a draft to the issue; no browser automation bypass.
"""
import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

from agent import Database
from growth.engage import get_credentials, send_reply, verify_meta_account
from growth.generator import compose
from growth.scoring import classify, normalize
from growth.voice import suitable_reply
from threads.publisher import thread_request

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
URL_PATTERN = re.compile(
    r"^/@(?P<author>[a-zA-Z0-9_.]{2,35})/post/(?P<code>[A-Za-z0-9_-]{5,30})/?$"
)
HEADER = "ENNA_PICK_V2"
MAX_EXCERPT = 1800
MAX_REPLIES_PER_REQUEST = 1


def parse_threads_url(value):
    """Normalize user supplied URLs, never fetch the Threads webpage."""
    if not isinstance(value, str) or len(value) > 400:
        raise ValueError("invalid_threads_permalink")
    url = urlparse(value.strip())
    if url.scheme != "https" or url.netloc.lower() not in (
            "threads.com", "www.threads.com", "threads.net", "www.threads.net"):
        raise ValueError("not_a_threads_post_url")
    match = URL_PATTERN.fullmatch(url.path)
    if not match:
        raise ValueError("must_use_canonical_@username_post_url")
    username = match.group("author").lower()
    if username == "dohay_dilam":
        raise ValueError("do_not_use_own_post_for_external_reply")
    code = match.group("code")
    # The public shortcode encodes a legacy numeric post ID. It is a HINT,
    # NOT trusted as a Meta API ID until GET /{id} confirms it.
    numeric = 0
    for char in code:
        numeric = numeric * 64 + ALPHABET.index(char)
    if len(str(numeric)) not in range(10, 29):
        raise ValueError("shortcode_not_a_verifiable_media_id")
    canonical = f"https://www.threads.com/@{username}/post/{code}"
    return {"username": username, "shortcode": code,
            "candidate_id": str(numeric), "url": canonical}


def decode_issue_body(body):
    if not isinstance(body, str) or len(body) > 4500:
        raise ValueError("invalid_issue_body")
    lines = body.strip().splitlines()
    if len(lines) != 3 or lines[0].strip() != HEADER:
        raise ValueError("not_an_enna_companion_issue")
    if not lines[1].startswith("THREADS_URL: ") or not lines[2].startswith("SELECTED_TEXT_BASE64URL: "):
        raise ValueError("unsupported_companion_issue_format")
    target = parse_threads_url(lines[1].split(": ", 1)[1])
    raw = lines[2].split(": ", 1)[1].strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{40,3500}", raw):
        raise ValueError("invalid_selected_text_encoding")
    try:
        text = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8").strip()
    except (ValueError, UnicodeDecodeError):
        raise ValueError("invalid_selected_text_encoding") from None
    if not 50 <= len(text) <= MAX_EXCERPT:
        raise ValueError("selected_post_excerpt_length_invalid")
    # Only relevant, benign public text can become a reply target.
    verdict = classify(text)
    if verdict["state"] != "candidate" or verdict["risk_flags"]:
        raise ValueError("not_relevant_or_safe_for_brand")
    return target, text, verdict


def verified_meta_target(info, target, selected, *, now=None):
    """Never publish unless the official Meta read matches owner selection."""
    if not isinstance(info, dict):
        return False
    if str(info.get("id") or "") != target["candidate_id"]:
        return False
    author = str(info.get("username") or "").lower().lstrip("@")
    if author != target["username"] or author == "dohay_dilam":
        return False
    permalink = str(info.get("permalink") or "")
    if not permalink or ("/post/" + target["shortcode"]) not in permalink:
        return False
    official = str(info.get("text") or "")
    if not 50 <= len(official) <= 2500 or classify(official)["state"] != "candidate":
        return False
    words = {x for x in normalize(selected).split() if len(x) > 2}
    actual = set(normalize(official).split())
    if len(words) < 6 or len(words & actual) / len(words) < 0.72:
        return False
    try:
        published = datetime.fromisoformat(
            str(info.get("timestamp")).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return False
    now = now or datetime.now(timezone.utc)
    if not timedelta(0) <= now - published <= timedelta(hours=96):
        return False
    return True


def can_send(text, selected, *, target):
    if not isinstance(text, str) or not 60 <= len(text.strip()) <= 380:
        return False
    return suitable_reply(text, selected) and not any(
        forbidden in normalize(text) for forbidden in (
            "follow", "theo doi", "ghé trang", "link bio", "tin nhan rieng",
            "mua ngay", "giam gia"))


def process(event, *, db=None, read=thread_request, create=compose,
            credentials=get_credentials, publish=send_reply, now=None):
    """Return an honest public-issue summary, never a claimed post without Meta ID."""
    now = now or datetime.now(timezone.utc)
    issue = event.get("issue") or {}
    repo = event.get("repository") or {}
    owner = str((repo.get("owner") or {}).get("login") or "")
    sender = str((event.get("sender") or {}).get("login") or "")
    issue_author = str((issue.get("user") or {}).get("login") or "")
    if not owner or owner != sender or owner != issue_author:
        return {"state":"not_project_owner"}
    title = str(issue.get("title") or "")
    if not title.startswith("enna-pick:"):
        return {"state":"not_enna_issue"}
    try:
        target, selected, verdict = decode_issue_body(issue.get("body"))
    except ValueError as exc:
        return {"state":"rejected_selection","reason":str(exc)}
    if title != "enna-pick:" + target["shortcode"]:
        return {"state":"title_target_mismatch"}

    db = db or Database()
    token_details = credentials(db)
    if token_details is None:
        return {"state":"meta_owner_permission_missing"}
    token, expected = token_details
    if expected != "dohay_dilam":
        return {"state":"meta_identity_mismatch"}
    verify_meta_account(token, expected)

    # AI generation happens only for this owner-selected post; no automated
    # discovery or scraping. Inputs are explicitly untrusted context.
    try:
        reply = create({
            "title": selected,
            "source_url": target["url"],
            "source": "owner_selected_public_threads_post",
            "niche": verdict["niche"],
        }, kind="reply_suggestion", prior_texts=())["post_text"].strip()
    except (ValueError, KeyError, TypeError, requests.RequestException):
        return {"state":"no_safe_draft"}
    if not can_send(reply, selected, target=target):
        return {"state":"no_safe_draft"}

    fallback = {"state":"draft_only_meta_cannot_verify_target",
                "draft":reply, "source_url":target["url"]}
    try:
        info = read("GET", "/" + target["candidate_id"], token,
            params={"fields":"id,username,text,timestamp,permalink"})
    except (requests.RequestException, ValueError):
        return fallback
    if not verified_meta_target(info, target, selected, now=now):
        return fallback

    # One authorized issue, one target, one author cooldown, daily cap shared
    # with external-keyword and own-account reply workers.
    fingerprint = hashlib.sha256(
        ("enna-dohay-selection:" + target["username"]).encode("utf-8")).hexdigest()
    claim = db.request("POST","/rpc/enna_claim_selected_reply",payload={
        "p_github_issue_id": int(issue["id"]),
        "p_target_post_id": target["candidate_id"],
        "p_author_fingerprint": fingerprint,
    })
    if not claim:
        return {"state":"duplicate_or_daily_limit","draft":reply,
                "source_url":target["url"]}
    attempt_id = claim[0]["attempt_id"]
    try:
        _, remote_id = publish(token, target["candidate_id"], reply)
        if not remote_id:
            raise RuntimeError("missing_reply_confirmation")
        db.patch("enna_companion_attempts",attempt_id,{
            "status":"posted","meta_reply_id":remote_id,
            "finished_at":datetime.now(timezone.utc).isoformat(),
        })
        return {"state":"posted_confirmed","source_url":target["url"],
                "reply_id":str(remote_id)}
    except Exception as exc:
        db.patch("enna_companion_attempts",attempt_id,{
            "status":"uncertain","error_kind":type(exc).__name__[:60],
            "finished_at":datetime.now(timezone.utc).isoformat(),
        })
        # Never attempt this post again automatically after an ambiguous write.
        return {"state":"uncertain_do_not_retry","source_url":target["url"]}


def safe_comment(result):
    """Owner receives a status. No credentials or raw Meta/API errors."""
    state=result.get("state","unknown")
    if state=="posted_confirmed":
        return ("✅ Enna đã nhận xác nhận phản hồi từ Meta. "
                "Mã phản hồi: `"+str(result.get("reply_id",""))+"`. "
                "Hãy kiểm tra dưới bài viết đã chọn.")
    if state=="draft_only_meta_cannot_verify_target":
        return ("🟠 Enna đã soạn bình luận nhưng Meta chưa cho phép xác minh "
                "bài mục tiêu qua API chính thức. **Không có bình luận tự động nào được đăng.**\n\n"
                "Bản nháp để bạn xem và tự đăng nếu phù hợp:\n\n> "+
                str(result.get("draft","")).replace("\n","\n> "))
    if state=="duplicate_or_daily_limit":
        return ("Enna không đăng: đã đạt giới hạn tương tác hoặc bài này đã "
                "được xử lý trước đó. Không tự thử lại.")
    if state=="uncertain_do_not_retry":
        return ("⚠️ Meta không trả về kết quả chắc chắn. Có thể bình luận đã "
                "được đăng. Enna sẽ **không gửi lại**; cần kiểm tra bài gốc.")
    return ("Enna không đăng bình luận. Trạng thái: `" +
            re.sub(r"[^a-z0-9_]", "", str(state))[:65] + "`. "
            "Không có hoạt động nào được ghi nhận là đã đăng.")


def comment_on_issue(issue_number, body):
    token = os.environ.get("GH_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo):
        return False
    url = "https://api.github.com/repos/" + repo + "/issues/" + str(issue_number) + "/comments"
    try:
        response = requests.post(url,headers={
            "Authorization":"Bearer "+token,
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28"},json={"body":body},timeout=15)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise SystemExit("GitHub owner issue event required")
    with open(event_path,encoding="utf-8") as f:
        event=json.load(f)
    try:
        result=process(event)
    except Exception as exc:
        # Never log secrets or raw user-selected text.
        result={"state":"unexpected_error_"+type(exc).__name__}
    issue=event.get("issue") or {}
    if issue.get("number") and result.get("state") not in ("not_project_owner","not_enna_issue"):
        comment_on_issue(issue["number"],safe_comment(result))
        # A real workflow event; do not treat a draft as a published reply.
        from growth.activity_log import emit
        run_id=os.environ.get("GITHUB_RUN_ID","")
        code=({"posted_confirmed":"companion_reply_posted",
               "draft_only_meta_cannot_verify_target":"companion_draft_only",
               "rejected_selection":"companion_rejected",
               "no_safe_draft":"companion_rejected"}).get(result.get("state"),"companion_checked")
        if run_id.isdecimal():
            try:
                emit(Database(),"growth",
                     "success" if code=="companion_reply_posted" else "skipped",
                     code,run_id=run_id)
            except Exception:
                pass
    print("Enna selected-post outcome:", result.get("state"))


if __name__=="__main__":
    main()
