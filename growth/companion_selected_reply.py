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
from difflib import SequenceMatcher
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

from agent import Database
from growth.engage import get_credentials, send_reply, verify_meta_account
from growth.companion_editor import (compose_selected, compose_selected_options, EnnaModelServiceError)
from growth.companion_judge import judge_selected
from growth.companion_fit import assess_selected, user_is_frustrated
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
    if len(lines) not in (3, 4) or lines[0].strip() != HEADER:
        raise ValueError("not_an_enna_companion_issue")
    if len(lines)==4 and lines[3].strip()!="ENNA_LOCAL_BROWSER_MODE: true":
        raise ValueError("unsupported_companion_handoff_mode")
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
    # Opt-in comes from the owner-created Issue; Chrome still independently
    # requires a private per-profile enabled switch and exact selected target.
    # Server never assumes the browser has posted or should be retried.
    verdict = {**verdict, "local_browser_mode": len(lines)==4}
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


# Generic words must never count as grounding for an auto-comment.
# This is a relevance check, NOT a restriction to office-related topics.
COMMON_CONTEXT_WORDS = frozenset({
    "mot","nhung","nguoi","ngay","viec","khong","minh","ban","cung",
    "chung","lam","dang","thay","duoc","nhieu","nhat","truoc","sau",
    "moi","dang","noi","cho","neu","theo","thoi","nghia","khac",
    "chinh","mot","nhat","that","cong","quan","trong","chuyen",
    "thanh","phai","phan","tiep","nhan","nhau","thuc","dieu",
})


def has_concrete_overlap(reply, original):
    """Require distinctive actual post details, not generic positivity.

    A compact reply may anchor in just one distinctive phrase from the
    original post. Semantic judging handles paraphrases, not word stuffing.
    """
    a = normalize(original).split()
    b = normalize(reply).split()
    selected = {t for t in a if len(t)>=4 and t not in COMMON_CONTEXT_WORDS}
    repeated = selected.intersection(
        t for t in b if len(t)>=4 and t not in COMMON_CONTEXT_WORDS)
    if len(repeated)<1:
        return False
    def pairs(seq):
        return {" ".join(seq[i:i+2]) for i in range(len(seq)-1)
                if len(seq[i])>=2 and len(seq[i+1])>=2
                and (seq[i] in selected or seq[i+1] in selected)}
    # Matching three independent generic words can still produce an entirely
    # irrelevant reply. Require an actual adjacent phrase from the source.
    return bool(pairs(a) & pairs(b))


def can_send(text, selected, *, target, semantic_override=False):
    if not isinstance(text, str) or not 60 <= len(text.strip()) <= 140:
        return False
    normalized = normalize(text)
    original_normalized=normalize(selected)
    # Reject extracts / near-verbatim copies and lifted profanity: a comment
    # must CONTRIBUTE, not merely repeat the author's original words.
    if re.search(r"\b(dm|dcm|dcmmm|vcl|dit me|vl)\b",normalized):
        return False
    # Do not praise a source of frustration as a fun/positive experience.
    if user_is_frustrated(selected) and any(x in normalized for x in (
        "co gang het minh", "them thu vi", "diem nhan",
        "nu cuoi", "loi khen", "tich cuc", "truyen cam hung",
        "doi khi chi can mot chut", "dang yeu", "niem vui"
    )):
        return False
    if normalized in original_normalized:
        return False
    # A selected public post is not evidence of theft, crime or coercion.
    # Prevent spurious accusations and ominous predictions in auto replies.
    claims=(
        "tranh trom", "de tranh trom", "trom cap", "an trom",
        "bi mat cap", "do trom", "mat do", "se mat do", "trom cho lam",
        "lay cap", "gian lan", "lua dao", "tu y lay", "dau doc"
    )
    if any(p in normalized and p not in original_normalized for p in claims):
        return False
    # A real reply must contribute new information or a fresh observation.
    # The previous model response copied three source phrases and supplied
    # only generic praise, despite passing the old overlap gate.
    source_tokens=original_normalized.split()
    reply_tokens=normalized.split()
    source_words=set(source_tokens)
    source_pairs=set(zip(source_tokens,source_tokens[1:]))
    novelty=sum(word not in source_words for word in reply_tokens)/max(1,len(reply_tokens))
    copied_pairs=sum(pair in source_pairs for pair in zip(reply_tokens,reply_tokens[1:]))/max(1,len(reply_tokens)-1)
    # One-sentence answers naturally reuse topic words; don't force filler
    # merely to hit an arbitrary proportion of new vocabulary.
    minimum_novelty = 0.23 if len(normalized) <= 140 else 0.33
    if novelty < minimum_novelty or copied_pairs > 0.38:
        return False
    # An open question about another person's future is not evidence of their
    # intention or gender. Don't invent certainty about employment tenure.
    if ("gan bo lau dai" in original_normalized or
        "nghi viec som" in original_normalized):
        if any(p in normalized for p in (
            "chac chan se gan bo", "co ve se gan bo lau dai",
            "khong phai nghi viec som", "khong nghi viec som dau",
            "se khong nghi viec", "se gan bo lau dai roi",
        )):
            return False
    if ("anh ay" in normalized and "anh ay" not in original_normalized):
        return False
    # Posts asking whether someone will remain employed invite jokes, NOT
    # unsupported certainty about that person's intentions or future.
    if any(p in original_normalized for p in (
        "gan bo lau dai","nghi viec som","nghi viec","roi di dau"
    )):
        if any(p in normalized for p in (
            "chac chan", "se khong muon roi", "se khong roi di",
            "khong muon roi di", "se o lai", "se khong nghi",
            "se gan bo", "khong muon nghi", "co ve ho se"
        )):
            return False
    longest=SequenceMatcher(None,original_normalized,normalized,
                            autojunk=False).find_longest_match(
                                0,len(original_normalized),0,len(normalized)).size
    if longest/max(1,len(normalized))>=0.56:
        return False
    # Reject generic filler that only summarizes the viral post rather than
    # contributing a distinctive observation. One draft revision is permitted.
    if any(phrase in normalized for phrase in (
        "that la mot khoanh khac", "dung la mot cau chuyen",
        "mot khoanh khac doi thuong ngot ngao",
        "nang luong tich cuc", "chi can mot nu cuoi",
        "truyen cam hung", "khoanh khac nho", "mong rang",
        "that dang yeu", "that y nghia", "bai hoc quy gia",
        "cuoc song doi khi", "ban that tuyet voi",
        "rat dang tran trong")):
        return False
    return ((semantic_override or has_concrete_overlap(text, selected))
            and suitable_reply(text, selected, require_niche=False,
                               require_overlap=not semantic_override,
                               max_chars=140)
            and not any(
        forbidden in normalize(text) for forbidden in (
            "follow", "theo doi", "ghé trang", "link bio", "tin nhan rieng",
            "mua ngay", "giam gia")))


def process(event, *, db=None, read=thread_request, create=compose_selected,
            credentials=get_credentials, publish=send_reply,
            direct_publish=direct_reply, allow_direct_trial=None,
            semantic_judge=judge_selected, option_generator=None, now=None):
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

    # The owner can request a safe, draft-only diagnosis using /enna draft.
    # This NEVER calls Meta, claims a posting attempt, or sends a reply.
    comment=event.get("comment") or {}
    draft_only=(
        str(comment.get("body") or "").strip()=="/enna draft"
        and str((comment.get("user") or {}).get("login") or "")==owner
    )
    def context_approved(candidate):
        # Hard safety checks remain mandatory even if an independent
        # semantic judge accepts a natural paraphrase.
        if can_send(candidate, selected, target=target):
            return True
        return (can_send(candidate, selected, target=target,
                         semantic_override=True)
                and semantic_judge(selected, candidate))

    def choose_alternatives(earlier=()):
        generator=(option_generator if option_generator is not None
                   else compose_selected_options if create is compose_selected
                   else None)
        if generator is None:
            return None
        try:
            options=generator({
                "title":selected,"niche":verdict["niche"],
                "source_url":target["url"]},earlier=tuple(earlier))
            if not isinstance(options,list):
                return None
            for option in options[:3]:
                if not isinstance(option,dict):
                    continue
                candidate=str(option.get("post_text") or "").strip()
                if candidate and context_approved(candidate):
                    return (candidate,str(option.get("content_angle") or "")[:220])
        except (requests.RequestException,ValueError,KeyError,TypeError):
            pass
        return None

    preapproved=False
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
    except EnnaModelServiceError as exc:
        return {"state":"ai_service_unavailable",
                "provider_reason":exc.safe_reason}
    except requests.RequestException:
        return {"state":"ai_service_unavailable","provider_reason":"transport_error"}
    except (ValueError, KeyError, TypeError):
        # Broken JSON, truncated model content or missing structured fields
        # must not abort the whole owner-requested task. One diversified
        # three-way alternative generation is attempted WITHOUT publishing.
        recovered=choose_alternatives(())
        if recovered is None:
            return {"state":"ai_draft_invalid_or_unavailable"}
        reply,content_angle=recovered
        preapproved=True
    if not preapproved and not context_approved(reply):
        # First try one targeted revision, then generate three DIFFERENT
        # grounded alternatives and independently review each. No Threads
        # write happens while exploring candidates.
        attempts=[reply]
        accepted=False
        try:
            second = create({
                "title": selected,
                "source_url": target["url"],
                "source": "owner_selected_public_threads_post",
                "niche": verdict["niche"],
                "quality_feedback": (
                    "Bản trước không đủ sát bài hoặc chưa góp được góc "
                    "nhìn mới. Viết MỘT câu thật NGẮN (60-120 ký tự), "
                    "bắt đúng MỘT chi tiết của bài để thêm một ý riêng. "
                    "Không tóm tắt, triết lý hay gượng gây hài."
                ),
            }, kind="reply_suggestion", prior_texts=(reply,))
            if second.get("should_reply") is False:
                return {"state":"not_worth_interjecting",
                        "content_angle":str(second.get("content_angle") or content_angle)[:220]}
            candidate=str(second.get("post_text") or "").strip()
            attempts.append(candidate)
            if context_approved(candidate):
                reply=candidate
                content_angle=str(second.get("content_angle") or content_angle)[:220]
                accepted=True
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass
        if not accepted:
            recovered=choose_alternatives(attempts)
            if recovered is not None:
                reply,content_angle=recovered
                accepted=True
        if not accepted:
            return {"state":"ai_reply_not_contextual_enough",
                    "content_angle":content_angle}

    if draft_only:
        return {"state":"draft_prepared_only","draft":reply,
                "source_url":target["url"],"content_angle":content_angle}
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
        if permitted and not verdict.get("local_browser_mode") and is_recent and target_read_limited(exc):
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
    if state=="draft_prepared_only":
        # A draft-only GitHub command MUST NOT be consumed by existing
        # Chrome AutoReply clients as a fresh publishable handoff.
        # In particular, do not use their recognized draft marker text.
        return ("🧪 KIỂM THỬ NỘI DUNG, KHÔNG ĐĂNG THREADS. "
                "Lệnh /enna draft chỉ dành để kiểm tra khả năng biên tập. "
                "Không coi kết quả này là lệnh tự đăng.\n\n"
                "Nội dung tham khảo (chỉ kiểm tra):\n\n> "
                +str(result.get("draft","")).replace("\n","\n> ")
                +angle_note)
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
        reason=str(result.get("provider_reason") or "unknown")
        public={"provider_rate_limited_429":"Groq đang giới hạn tần suất (HTTP 429)",
                "provider_auth_or_access_401":"Groq từ chối khóa API (HTTP 401)",
                "provider_auth_or_access_403":"Groq từ chối quyền truy cập (HTTP 403)",
                "network_timeout":"Kết nối đến Groq hết thời gian",
                "network_error":"Không kết nối được Groq",
                "transport_error":"Lỗi kết nối Groq",
                "provider_http_400":"Groq từ chối định dạng yêu cầu (HTTP 400)",
                "provider_http_500":"Groq gặp lỗi máy chủ (HTTP 500)",
                "provider_http_502":"Groq gặp lỗi máy chủ (HTTP 502)",
                "provider_http_503":"Groq gặp lỗi máy chủ (HTTP 503)",
                "provider_http_504":"Groq gặp lỗi máy chủ (HTTP 504)"}
        return ("Enna đã nhận bài nhưng chưa tạo được bản nháp: "
                +public.get(reason,"lỗi dịch vụ AI ("+
                re.sub(r"[^a-z0-9_]", "",reason)[:40]+")")
                +". **Chưa có bình luận nào được đăng.**")
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
               "draft_prepared_only":"companion_draft_only",
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
