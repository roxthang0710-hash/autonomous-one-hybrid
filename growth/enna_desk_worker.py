"""Enna Desk — task-specific AI reasoning over real private evidence.

Existing GitHub Groq secret runs the model. This worker never publishes social
posts, sends replies, changes credentials or spends money. A task is marked
completed only after a validated model response has actually been stored.
"""
import json
import os
import re
from difflib import SequenceMatcher
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from agent import Database

import requests

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
QUEUED_MODELS = ("awaiting_model_v2", "rule_based_multi_role", "groq_multi_role_partial")
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "direct_answer": {"type": "string"},
        "verified_findings": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 4},
        "actions": {"type": "array", "minItems": 3, "maxItems": 5, "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "action": {"type": "string"}, "rationale": {"type": "string"},
                "executor": {"type": "string", "enum": ["enna", "owner", "joint"]},
                "success_check": {"type": "string"},
                "status": {"type": "string", "enum": ["proposed", "needs_permission"]},
            },
            "required": ["action", "rationale", "executor", "success_check", "status"],
        }},
        "role_summaries": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "analyst": {"type": "string"}, "strategist": {"type": "string"},
                "operator": {"type": "string"},
            },
            "required": ["analyst", "strategist", "operator"],
        },
        "unknowns": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    },
    "required": ["direct_answer", "verified_findings", "actions", "role_summaries", "unknowns"],
}


def is_vi(sentence):
    return isinstance(sentence, str) and bool(re.search(
        r"[àáạảãăắặằẳẵâấậầẩẫđèéẹẻẽêếệềểễìíịỉĩòóọỏõôốộồổỗơớợờởỡùúụủũưứựừửữỳýỵỷỹ]",
        sentence.lower()))


def is_prompt_echo(answer, question):
    """Reject answers that merely restate the user's words."""
    def clean(x):
        return re.sub(r"[^a-z0-9à-ỹđ ]", " ", x.lower()).strip()
    a,b=clean(answer),clean(question)
    if not a or not b:
        return True
    ratio=SequenceMatcher(None,a,b).ratio()
    # Prefix/sentence repetition matters even when boilerplate is added.
    return ratio >= 0.66 or (a.startswith(b[:min(90,len(b))]) and len(a)<len(b)*2)


def verified_facts(evidence):
    """Facts come from source rows, not language-model guesses."""
    facts=[]
    snapshots=evidence.get("follower_snapshots") or []
    valid=[s for s in snapshots if isinstance(s.get("followers"),int) and s["followers"]>=0]
    if valid:
        f=valid[0]
        age=f.get("age_days")
        freshness=" (dữ liệu quá hạn)" if age is None or age>1 else " (mốc mới nhất được lưu)"
        facts.append(f"Supabase ghi nhận {f['followers']} follower ngày {f.get('measured_on','không rõ')}{freshness}; đây không nhất thiết là số hiện tại.")
    else:
        facts.append("Chưa có số follower được xác minh trong dữ liệu đang đọc.")
    states=evidence.get("threads_status_counts") or {}
    facts.append(f"Ledger Threads: {states.get('posted',0)} ghi nhận đã đăng, {states.get('scheduled_external',0)} lên lịch ngoài và {states.get('queued',0)} đang chờ; chưa đủ để suy ra follower mới.")
    posts=evidence.get("top_measured_posts") or []
    if posts:
        post=posts[0]
        facts.append(f"Bài có số lượt xem cao nhất trong mẫu: {post.get('views','chưa rõ')} view, {post.get('likes','chưa rõ')} lượt thích; chưa xác minh lượt theo dõi do bài này tạo ra.")
    media=evidence.get("media_ready_by_type") or {}
    facts.append(f"Kho media: {media.get('original_meme',0)} meme gốc có tệp sẵn sàng, {media.get('original_video',0)} video có tệp sẵn sàng.")
    return facts[:4]


def eligible(row):
    return (isinstance(row, dict) and row.get("model_used") in QUEUED_MODELS and
            row.get("status") in ("running", "completed") and
            int(row.get("analysis_attempts") or 0)<3 and
            isinstance(row.get("request_text"), str) and
            8 <= len(row["request_text"]) <= 1200)


def safe_get(db, table, **params):
    try:
        records = db.request("GET", "/" + table, params=params)
        return records if isinstance(records, list) else []
    except (requests.RequestException, ValueError):
        return []


def evidence_snapshot(db, current):
    """Bounded fresh read. Old cached snapshot is NOT a substitute for provider data."""
    growth = safe_get(db, "growth_metricool_daily", select="measured_on,followers,post_views,new_followers,interactions",
                      order="measured_on.desc", limit="10")
    threads = safe_get(db, "threads_posts",
        select="id,status,scheduled_at,published_at,platform_post_id,permalink,topic_tag_requested,topic_tag_planned,media_url,text_content",
        order="scheduled_at.desc", limit="70")
    metrics = safe_get(db, "threads_metrics",
        select="post_id,views,likes,replies,reposts,collected_at",
        order="collected_at.desc",limit="100")
    metric_by_id = {}
    for row in metrics:
        metric_by_id.setdefault(row.get("post_id"), row)
    top_posts = []
    for row in threads:
        metric = metric_by_id.get(row.get("id"), {})
        if metric.get("views") is None:
            continue
        top_posts.append({"text_excerpt":str(row.get("text_content") or "")[:130],
                          "views":metric.get("views"),"likes":metric.get("likes"),
                          "replies":metric.get("replies"),"collected_at":metric.get("collected_at"),
                          "post_status":row.get("status")})
    top_posts.sort(key=lambda x: x.get("views") or 0,reverse=True)
    attempts = safe_get(db, "enna_companion_attempts",
        select="status,error_kind,attempted_at,meta_reply_id", order="attempted_at.desc", limit="5")
    media = safe_get(db, "enna_media_ideas",
        select="media_type,status,source_url",order="created_at.desc",limit="40")
    publication = safe_get(db,"enna_publication_evidence",
        select="provider_status,checked_at,meta_post_id",order="checked_at.desc",limit="30")
    history = safe_get(db,"enna_desk_tasks",
        select="request_text,response,model_used,created_at",
        order="created_at.desc",limit="7")
    events = safe_get(db,"enna_activity_events",
        select="kind,code,status,occurred_at",order="occurred_at.desc",limit="20")
    now=datetime.now(timezone.utc)
    local_today=now.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    growth_out=[]
    for x in growth[:6]:
        day=x.get("measured_on")
        try:
            age=(local_today-datetime.fromisoformat(str(day)).date()).days
        except (ValueError,TypeError):
            age=None
        growth_out.append({**x,"age_days":age})
    return {
        "checked_at":now.isoformat(),
        "local_date":local_today.isoformat(),
        "follower_snapshots":growth_out,
        "threads_status_counts":{s:sum(x.get("status")==s for x in threads)
             for s in ("posted","scheduled_external","queued","uncertain")},
        "native_topic_requested_confirmed_in_ledger":sum(
            x.get("status")=="posted" and bool(x.get("topic_tag_requested")) for x in threads),
        "native_topic_visually_confirmed":False,
        "top_measured_posts":top_posts[:6],
        "reply_attempts":attempts,
        "media_ready_by_type":{
            "original_meme":sum(x.get("media_type")=="original_meme" and x.get("status")=="ready" and bool(x.get("source_url")) for x in media),
            "original_video":sum(x.get("media_type") in ("video","original_video") and x.get("status")=="ready" and bool(x.get("source_url")) for x in media)
        },
        "publication_evidence":publication[:8],
        "recent_failures":[x for x in events if x.get("status")=="failed"][:5],
        "previous_requests":[x.get("request_text","")[:240] for x in history if x.get("request_text")!=current["request_text"]][:4],
        "source_limits":"Supabase snapshots may be stale or omit Metricool external publications. No proof of follower conversion without provider-level metrics."
    }


def call_model(task, evidence, *, api=requests.post):
    key=os.getenv("GROQ_API_KEY","").strip()
    if not key:
        raise RuntimeError("groq_key_unavailable")
    prompt={
        "current_request":task["request_text"],
        "task_kind":task["kind"],
        "evidence":evidence,
        "decision_goal":"Answer the owner's exact concern, not a generic growth report."
    }
    guidance=(
        "Bạn là Enna, AI Agent điều phối kênh Threads Đồ Hay Đi Làm. Trả lời 100% bằng "
        "tiếng Việt tự nhiên (không dùng tiếng Anh trong phần câu trả lời). "
        "Đây là vấn đề thực tế cần giải quyết, không phải bài tập viết lời khuyên. "
        "Trả lời trực tiếp câu hỏi cụ thể, xem lại những câu hỏi trước để KHÔNG lặp lại. "
        "QUAN TRỌNG: Không được nhắc lại hoặc chép lại nguyên văn câu hỏi trong direct_answer. "
        "Trường direct_answer KHÔNG được chứa chữ số hoặc con số thống kê; các dữ kiện định lượng "
        "được viết bởi hệ thống từ nguồn đã xác minh. Tập trung giải thích vấn đề và hướng xử lý. "
        "Không được kết luận chắc chắn không có CTA, Topic, meme, trả lời hay video chỉ từ những mẫu thiếu dữ liệu. "
        "Không khẳng định lịch ngoài Metricool chưa xuất bản; trạng thái scheduled_external có thể đã đăng qua nhà cung cấp. "
        "Không được suy ra follower tăng từ số lượt xem nếu không có số liệu chuyển đổi. "
        "Bài đã yêu cầu topic_tag chưa đồng nghĩa đã hiển thị Topic thành công. "

        "Phần direct_answer phải giải thích nguyên nhân khả dĩ có điều kiện, điểm nghẽn cụ thể, "
        "và trả lời việc Enna tự thực hiện được ngay. Không được nói chỉ cần đăng đều là sẽ tăng follow. "
        "Bắt đầu như: Có 3 vấn đề đã thấy..., không mở đầu bằng cách trích câu của người dùng. "
        "Phân tích dựa trên bằng chứng; phân biệt dữ liệu cũ, thiếu dữ liệu và kết quả thật. "
        "Nêu ít nhất 2 hành động ngoài đăng bài: có thể là cải thiện hồ sơ/bio, xây cộng đồng "
        "chính thống, nội dung gốc có tính chia sẻ, hợp tác tự nguyện, chủ động phân phối vào Topic, "
        "đo hiệu quả CTA, thử nội dung rồi phản hồi. Chỉ chọn giải pháp phù hợp câu hỏi hiện tại. "
        "Ưu tiên cụ thể: bước đầu tiên, ai làm, điều kiện kiểm tra, tín hiệu thất bại, phương án thay thế. "
        "Nhiệm vụ hiện tại chỉ là PHÂN TÍCH; không nói đã đăng, sửa, kết nối, bình luận hoặc tạo media "
        "nếu dữ liệu không chứng minh. Đừng nói lịch đăng nhiều là bằng chứng tăng follower. "
        "Nêu vấn đề truy cập hoặc quyền nếu thật sự cần. Không yêu cầu người dùng test vô lý. "
        "Không gắn thẻ tài khoản không liên quan, spam, mua người theo dõi, dùng tài khoản giả. "
        "Các vai trò analyst/strategist/operator là ba góc nhìn của một lượt tổng hợp AI, "
        "không được giả vờ là ba AI độc lập đã thực thi công việc. "
        "Với nguồn số liệu quá hạn, hãy nêu điều chắc chắn và vẫn đề xuất thí nghiệm khả thi."
    )
    resp=api("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":"Bearer "+key,"content-type":"application/json"},
        json={
            "model":MODEL, "temperature":0.36, "max_completion_tokens":3200,
            "reasoning_effort":"high",
            "response_format":{"type":"json_schema","json_schema":{
                "name":"enna_task_specific_reasoning_v2","strict":True,"schema":SCHEMA}},
            "messages":[{"role":"system","content":guidance},
                        {"role":"user","content":json.dumps(prompt,ensure_ascii=False)}],
        },timeout=65)
    resp.raise_for_status()
    result=json.loads(resp.json()["choices"][0]["message"]["content"])
    if not isinstance(result,dict) or set(result)!=set(SCHEMA["required"]):
        raise ValueError("invalid_schema")
    if not is_vi(result.get("direct_answer")) or not 80<=len(result["direct_answer"])<=1300:
        raise ValueError("answer_not_specific_vietnamese")
    if is_prompt_echo(result["direct_answer"],task["request_text"]):
        raise ValueError("answer_echoes_user_question")
    if re.search(r"\d",result["direct_answer"]):
        raise ValueError("unsupported_numeric_claim_in_summary")
    # Strong factual negations may be hallucinations when some provider events are
    # missing from the ledger. They need confirmation, not confident prose.
    if re.search(r"(không có|chưa có)\s+(?:meme|topic|chủ đề|cta|bình luận|video)",result["direct_answer"].lower()):
        raise ValueError("unsupported_absolute_claim")
    findings=result.get("verified_findings")
    if not isinstance(findings,list) or not 1<=len(findings)<=4:
        raise ValueError("findings_invalid")
    actions=result.get("actions")
    if not isinstance(actions,list) or not 3<=len(actions)<=5:
        raise ValueError("actions_invalid")
    for a in actions:
        if not isinstance(a,dict) or set(a)!=set(SCHEMA["properties"]["actions"]["items"]["required"]):
            raise ValueError("action_schema")
        if a.get("executor") not in ("enna","owner","joint") or a.get("status") not in ("proposed","needs_permission"):
            raise ValueError("action_scope")
        if not all(isinstance(a.get(k),str) and 8<=len(a[k])<=330
                   for k in ("action","rationale","success_check")):
            raise ValueError("action_not_concrete")
    outside_posts=sum(not re.search(r"\bđăng\s+(?:bài|threads|nội dung)\b",a["action"].lower()) for a in actions)
    if outside_posts < 2:
        raise ValueError("lacks_nonposting_growth_actions")
    summaries=result.get("role_summaries")
    if not isinstance(summaries,dict) or set(summaries)!={"analyst","strategist","operator"}:
        raise ValueError("role_summaries_invalid")
    if not all(is_vi(s) and 15<=len(s)<=400 for s in summaries.values()):
        raise ValueError("role_summaries_not_vietnamese")
    if not isinstance(result.get("unknowns"),list) or len(result["unknowns"])>3:
        raise ValueError("unknowns_invalid")
    return result


def upgrade(task, evidence, model_call=call_model):
    reply=model_call(task,evidence)
    prior=task.get("response") if isinstance(task.get("response"),dict) else {}
    return {
        "kind":task["kind"],
        "request":task["request_text"],
        "evidence":evidence,
        "direct_answer":reply["direct_answer"],
        "verified_findings":verified_facts(evidence),
        "action_plan":reply["actions"],
        "unknowns":reply["unknowns"],
        "roles":[{"role":role,"status":"completed","summary":reply["role_summaries"][role],
                  "actions":[],"risks":[]} for role in ("analyst","strategist","operator")],
        "engine":"groq_task_specific_v2",
        "capability_note":"Phân tích AI dựa trên số liệu; chưa thực hiện các đề xuất hoặc đăng/bình luận từ nhiệm vụ này.",
        "previous_response_replaced":bool(prior)
    }


def run(db=None):
    if not os.getenv("GROQ_API_KEY","").strip():
        return "groq_key_unavailable"
    db=db or Database()
    pending=db.request("GET","/enna_desk_tasks",params={
        "select":"id,kind,request_text,status,response,model_used,analysis_attempts,analysis_last_attempt_at",
        "model_used":"in.(awaiting_model_v2,rule_based_multi_role,groq_multi_role_partial)",
        "order":"created_at.asc","limit":"3"})
    if not isinstance(pending,list) or not pending:
        return "no_pending_tasks"
    done=0
    for task in pending:
        if not eligible(task):
            continue
        last=task.get("analysis_last_attempt_at")
        if last:
            try:
                last_time=datetime.fromisoformat(str(last).replace("Z","+00:00"))
                if (datetime.now(timezone.utc)-last_time).total_seconds()<180:
                    continue
            except (ValueError,TypeError):
                pass
        try:
            evidence=evidence_snapshot(db,task)
            answer=upgrade(task,evidence)
        except (requests.RequestException,ValueError,KeyError,TypeError,RuntimeError) as error:
            # Never falsely report completed or replace a prior response with a template.
            attempts=int(task.get("analysis_attempts") or 0)+1
            reason="ai_quality_rejected" if isinstance(error,ValueError) else "ai_backend_unavailable"
            print("Enna model response not verified:",reason,"attempt",attempts)
            failed=attempts>=3
            db.request("PATCH","/enna_desk_tasks",params={
                "id":"eq."+str(task["id"]),"model_used":"eq."+str(task["model_used"])},
                payload={
                    "status":"failed" if failed else "running",
                    "model_used":"model_quality_failed" if failed else "awaiting_model_v2",
                    "analysis_attempts":attempts,
                    "analysis_last_attempt_at":datetime.now(timezone.utc).isoformat(),
                    "error_code":reason,
                    **({"finished_at":datetime.now(timezone.utc).isoformat()} if failed else {})
                })
            continue
        changed=db.request("PATCH","/enna_desk_tasks",
            params={"id":"eq."+str(task["id"]),"model_used":"eq."+str(task["model_used"])},
            payload={
                "status":"completed","response":answer,
                "model_used":"groq_task_specific_v2","error_code":None,
                "analysis_attempts":int(task.get("analysis_attempts") or 0)+1,
                "analysis_last_attempt_at":datetime.now(timezone.utc).isoformat(),
                "finished_at":datetime.now(timezone.utc).isoformat(),
            },prefer="return=representation")
        if changed:
            done+=1
    return f"model_verified_responses={done}"


if __name__=="__main__":
    print("Enna Desk reasoning upgrade:",run())
