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
from growth.companion_editor import compose_selected
from growth.companion_fit import assess_selected
from growth.selected_direct_reply import (
    ConfirmedMetaRejection, MetaStageError, direct_reply, target_read_limited,
)
from growth.scoring import normalize
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
    # The post is owner-selected. Broad context is welcome; keywords are
    # optional. Maintain independent privacy/safety checks.
    verdict = assess_selected(text)
    if verdict["state"] != "candidate":
        raise ValueError("unsafe_or_insufficient_selected_context")
    return target, text, verdict


def clean_selected_excerpt(text):
    """Remove incidental Threads UI controls, never infer or rewrite the story."""
    lines = []
    for item in str(text or "").splitlines():
        line = item.strip()
        if not line:
            continue
        if "✳ Gửi Enna" in line:
            # The injected button is NOT part of the author's post.
            line = line.replace("✳ Gửi Enna", "").strip()
        if re.fullmatch(r"\d+\s*(giờ|phút|ngày|tuần)\s*(trước)?", line,
                        flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"\d+(?:[,.]\d+)?[KkMm]?", line):
            # A stand-alone engagement counter, not evidence of virality.
            continue
        if line:
            lines.append(line)
    return "\n".join(lines)[:1800].strip()


def parse_owner_issue_time(value):
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return stamp.astimezone(timezone.utc) if stamp.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


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
    if not 30 <= len(official) <= 2500 or assess_selected(official[:1800])["state"] != "candidate":
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
    normalized = normalize(text)
    # Reject generic filler that only summarizes the viral post rather than
    # contributing a distinctive observation. One draft revision is permitted.
    if any(phrase in normalized for phrase in (
        "that la mot khoanh khac", "dung la mot cau chuyen",
        "mot khoanh khac doi thuong ngot ngao")):
        return False
    return suitable_reply(text, selected, require_niche=False) and not any(
        forbidden in normalize(text) for forbidden in (
            "follow", "theo doi", "ghé trang", "link bio", "tin nhan rieng",
            "mua ngay", "giam gia"))


def process(event, *, db=None, read=thread_request, create=compose_selected,
            credentials=get_credentials, publish=send_reply,
            direct_publish=direct_reply, allow_direct_trial=None, now=None):
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
    # Do not let Chrome's UI button or isolated engagement counts pollute the
    # AI context. This works even with the existing v0.3/v0.4 extension.
    selected = clean_selected_excerpt(selected)
    if assess_selected(selected)["state"] != "candidate":
        return {"state":"insufficient_clean_context"}

    db = db or Database()

    # AI generation happens only for this owner-selected post; no automated
    # discovery or scraping. Inputs are explicitly untrusted context.
    try:
        proposed = create({
            "title": selected,
            "source_url": target["url"],
            "source": "owner_selected_public_threads_post",
            "niche": verdict["niche"],
        }, kind="reply_suggestion", prior_texts=())
        if proposed.get("should_reply") is False:
            return {"state":"not_worth_interjecting",
                    "content_angle":str(proposed.get("content_angle") or "")[:220]}
        reply = proposed["post_text"].strip()
        content_angle = str(proposed.get("content_angle") or "")[:220]
    except requests.RequestException:
        return {"state":"ai_service_unavailable"}
    except (ValueError, KeyError, TypeError):
        return {"state":"ai_draft_invalid_or_unavailable"}
    if not can_send(reply, selected, target=target):
        # One more safe drafting pass if the first comment is too generic.
        # This cannot initiate a Meta publish or multiply interaction attempts.
        try:
            second = create({
                "title": selected,
                "source_url": target["url"],
                "source": "owner_selected_public_threads_post",
                "niche": verdict["niche"],
            }, kind="reply_suggestion", prior_texts=(reply,))
            if second.get("should_reply") is False:
                return {"state":"not_worth_interjecting",
                        "content_angle":str(second.get("content_angle") or content_angle)[:220]}
            replacement = str(second.get("post_text") or "").strip()
            if can_send(replacement, selected, target=target):
                reply = replacement
                content_angle = str(second.get("content_angle") or content_angle)[:220]
            else:
                return {"state":"ai_reply_not_contextual_enough",
                        "content_angle":content_angle}
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return {"state":"ai_reply_not_contextual_enough",
                    "content_angle":content_angle}

    fallback = {"state":"draft_only_meta_cannot_verify_target",
                "draft":reply, "source_url":target["url"],
                "content_angle":content_angle}
    # Draft first, check Meta authorization second. Missing/expired OAuth must
    # not discard a useful draft or force the owner to resend the same story.
    try:
        token_details = credentials(db)
        if token_details is None:
            return {**fallback,"state":"draft_only_meta_not_authorized"}
        token, expected = token_details
        if expected != "dohay_dilam":
            return {**fallback,"state":"draft_only_meta_identity_mismatch"}
        verify_meta_account(token, expected)
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return {**fallback,"state":"draft_only_meta_not_authorized"}
    direct_trial = False
    try:
        info = read("GET", "/" + target["candidate_id"], token,
            params={"fields":"id,username,text,timestamp,permalink"})
    except requests.HTTPError as exc:
        permitted = (allow_direct_trial if allow_direct_trial is not None
                     else os.getenv("ENNA_OWNER_SELECTED_DIRECT_REPLY_TRIAL", "").lower()=="true")
        # Owner explicitly selected this exact public post; for this narrow
        # owner-initiated request only, a Graph READ-scope denial does not
        # necessarily imply a WRITE-scope denial. Try official Meta WRITE once.
        # NEVER try if Graph returns unexpected/mismatched content or 5xx.
        created_at = parse_owner_issue_time(issue.get("created_at"))
        is_recent = bool(created_at and timedelta(0)<=now-created_at<=timedelta(hours=48))
        if permitted and is_recent and target_read_limited(exc):
            direct_trial = True
        else:
            return fallback
    except (requests.RequestException, ValueError):
        return fallback
    else:
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
        if direct_trial:
            _, remote_id = direct_publish(token, target["candidate_id"], reply)
        else:
            _, remote_id = publish(token, target["candidate_id"], reply)
        if not remote_id:
            raise RuntimeError("missing_reply_confirmation")
        db.patch("enna_companion_attempts",attempt_id,{
            "status":"posted","meta_reply_id":remote_id,
            "finished_at":datetime.now(timezone.utc).isoformat(),
        })
        return {"state":"posted_confirmed","source_url":target["url"],
                "reply_id":str(remote_id),"content_angle":content_angle,
                "verification":"meta_publish_confirmed" if direct_trial else "meta_read_and_publish"}
    except ConfirmedMetaRejection as exc:
        # A definitive refusal on the first official Meta create call means
        # there is NO published reply. The atomic claim remains consumed.
        db.patch("enna_companion_attempts",attempt_id,{
            "status":"meta_rejected",
            "error_kind":"HTTP_"+str(exc.http_status),
            "finished_at":datetime.now(timezone.utc).isoformat(),
        })
        return {"state":"meta_rejected_direct_reply","draft":reply,
                "source_url":target["url"],"content_angle":content_angle,
                "http_status":exc.http_status}
    except MetaStageError as exc:
        # A 5xx response on container creation, or any failure after that
        # boundary, must be considered ambiguous. Persist safe stage only.
        safe_stage = "meta_" + exc.stage + "_HTTP_" + str(exc.http_status)
        db.patch("enna_companion_attempts",attempt_id,{
            "status":"uncertain","error_kind":safe_stage[:60],
            "finished_at":datetime.now(timezone.utc).isoformat(),
        })
        return {"state":"uncertain_do_not_retry","source_url":target["url"],
                "meta_stage":exc.stage}
    except Exception as exc:
        db.patch("enna_companion_attempts",attempt_id,{
            "status":"uncertain","error_kind":type(exc).__name__[:60],
            "finished_at":datetime.now(timezone.utc).isoformat(),
        })
        # Never attempt this post again automatically after an ambiguous write.
        return {"state":"uncertain_do_not_retry","source_url":target["url"]}


def safe_comment(result):
    """Owner sees accurate outcome and an optional *original* content angle."""
    state=result.get("state","unknown")
    angle=str(result.get("content_angle") or "").strip()[:220]
    angle_note=("\n\nGóc nội dung riêng Enna có thể phát triển: "+angle) if angle else ""
    if state=="posted_confirmed":
        return ("✅ Enna đã nhận xác nhận phản hồi từ Meta. "
                "Mã phản hồi: `"+str(result.get("reply_id",""))+"`. "
                "Hãy kiểm tra dưới bài viết đã chọn."+angle_note)
    if state in ("draft_only_meta_not_authorized","draft_only_meta_identity_mismatch"):
        return ("🟠 Enna đã tạo bản nháp nhưng tài khoản chưa xác nhận được "
                "quyền OAuth để đăng. **Chưa có bình luận nào được đăng.**"
                "\n\nBản nháp để bạn tự sử dụng nếu phù hợp:\n\n> "
                +str(result.get("draft","")).replace("\n","\n> ")+angle_note)
    if state=="draft_only_meta_cannot_verify_target":
        return ("🟠 Enna đã soạn bình luận nhưng Meta chưa cho phép xác minh "
                "bài mục tiêu qua API chính thức. **Không có bình luận tự động nào được đăng.**\n\n"
                "Bản nháp để bạn xem và tự đăng nếu phù hợp:\n\n> "+
                str(result.get("draft","")).replace("\n","\n> ")+angle_note)
    if state=="not_worth_interjecting":
        return ("Enna đã phân tích bài bạn chọn nhưng không thấy cách "
                "bình luận tự nhiên có ích. **Không đăng bình luận.**"+angle_note)
    if state=="meta_rejected_direct_reply":
        return ("🟠 Enna đã thử đăng MỘT lần bằng API Threads chính thức, "
                "nhưng Meta từ chối tạo bình luận (HTTP "
                +str(result.get("http_status") or "lỗi")+
                "). **Không có bình luận nào được đăng, không tự thử lại.**"
                "\n\nBản nháp nếu bạn muốn dùng thủ công:\n\n> "
                +str(result.get("draft","")).replace("\n","\n> ")+angle_note)
    if state=="ai_service_unavailable":
        return ("Enna đã nhận bài nhưng dịch vụ tạo nội dung chưa phản hồi "
                "thành công. **Không có bình luận nào được đăng.** "
                "Vui lòng gửi một bài khác khi dịch vụ hoạt động lại.")
    if state=="ai_draft_invalid_or_unavailable":
        return ("Enna đã nhận bài nhưng bản nháp AI không đạt kiểm tra "
                "định dạng hoặc không có cấu hình mô hình khả dụng. "
                "**Không có bình luận nào được đăng.**")
    if state=="ai_reply_not_contextual_enough":
        return ("Enna đã soạn nội dung nhưng bộ kiểm tra không thấy "
                "bình luận bám đủ sát bài gốc. **Không tự đăng**."
                +angle_note)
    if state=="duplicate_or_daily_limit":
        return ("Enna không đăng: đã đạt giới hạn tương tác hoặc bài này đã "
                "được xử lý trước đó. Không tự thử lại."+angle_note)
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
               "draft_only_meta_not_authorized":"companion_draft_only",
               "draft_only_meta_identity_mismatch":"companion_draft_only",
               "rejected_selection":"companion_rejected",
               "no_safe_draft":"companion_rejected",
               "ai_service_unavailable":"companion_rejected",
               "meta_rejected_direct_reply":"companion_draft_only",
               "ai_draft_invalid_or_unavailable":"companion_rejected",
               "ai_reply_not_contextual_enough":"companion_rejected"}).get(result.get("state"),"companion_checked")
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
