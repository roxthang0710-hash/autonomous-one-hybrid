"""Enna Clone scheduled text-only tasks; ZERO access to original Enna accounts.

Run by isolated GitHub Actions workflow. No publishing, email, external
connectors, shell tools, or unbounded loops. The server's DB RPC atomically
claims due tasks and advances next_run before requesting the AI provider.
A run failure is recorded as a failure, never silently retried in a loop.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

MODEL="openai/gpt-oss-20b"
GROQ_ENDPOINT="https://api.groq.com/openai/v1/chat/completions"
MAX_CLAIM=4
MAX_REPLY_TOKENS=850

class CloneWorker:
    def __init__(self, url=None, service_key=None, groq_key=None, model=None):
        self.url=(url or os.getenv("SUPABASE_URL","")).rstrip("/")
        self.key=service_key or os.getenv("DB_SERVICE_KEY","")
        self.groq=groq_key or os.getenv("ENNA_CLONE_GROQ_API_KEY","")
        self.model=model or os.getenv("GROQ_MODEL",MODEL)
        if not self.url.startswith("https://") or not self.key:
            raise ValueError("Missing trusted server database configuration")

    def db(self,path,method="GET",body=None):
        raw=None if body is None else json.dumps(body,ensure_ascii=False).encode("utf-8")
        req=Request(
          self.url+"/rest/v1/"+path,
          data=raw,method=method,
          headers={"apikey":self.key,"Authorization":"Bearer "+self.key,
                   "Content-Type":"application/json",
                   "Prefer":"return=representation"}
        )
        with urlopen(req,timeout=12) as res:
            data=res.read(200000)
        return json.loads(data.decode("utf-8")) if data else None

    def model_reply(self,prompt):
        if not self.groq:
            raise RuntimeError("Groq not configured")
        request=[
            {"role":"system","content":
             "Bạn là Enna Clone cá nhân. Viết tiếng Việt, chỉ tạo bản nháp "
             "cho một nhiệm vụ người dùng đã cho. Không đọc email, lịch, "
             "Internet hoặc tài liệu khác. Không tự khẳng định đã làm "
             "hành động ngoài ứng dụng. Không bịa số, link, người hoặc hạn. "
             "Nếu thiếu dữ liệu, ghi 'Chưa xác nhận'. Tóm tắt đầu ra rõ ràng "
             "và kết thúc bằng phần Những điều cần người dùng kiểm tra."},
            {"role":"user","content":prompt},
        ]
        req=Request(
          GROQ_ENDPOINT,
          data=json.dumps({"model":self.model,"messages":request,
                           "max_tokens":MAX_REPLY_TOKENS,"temperature":0.25}).encode(),
          method="POST",
          headers={"Authorization":"Bearer "+self.groq,
                   "Content-Type":"application/json"},
        )
        with urlopen(req,timeout=24) as res:
            data=json.loads(res.read(160000))
        content=data.get("choices",[{}])[0].get("message",{}).get("content","")
        if not isinstance(content,str) or not content.strip():
            raise RuntimeError("Model returned no answer")
        return content.strip()[:11000]

    def run_once(self):
        # DB claim checks schedules feature flag AND approved beta access.
        tasks=self.db("rpc/enna_clone_claim_due","POST",{"p_limit":MAX_CLAIM}) or []
        results=[]
        for task in tasks[:MAX_CLAIM]:
            owner=task["owner_id"]
            task_id=task["id"]
            status="skipped"
            summary="Chưa thực hiện vì giới hạn lượt."
            try:
                credited=self.db("rpc/enna_clone_reserve_request","POST",{
                    "p_owner":owner,"p_daily_limit":4,"p_global_limit":40
                })
                if credited is True:
                    prompt=str(task.get("instruction") or "")
                    if 8<=len(prompt)<=1800:
                        status="complete"
                        summary=self.model_reply(prompt)
                    else:
                        status="failed"
                        summary="Nhiệm vụ không hợp lệ; cần chỉnh nội dung."
            except (HTTPError,URLError,OSError,ValueError,RuntimeError,KeyError,IndexError):
                status="failed"
                summary="Dịch vụ chưa hoàn thành. Hãy kiểm tra nhật ký hoặc cấu hình để xử lý."
            record={
              "owner_id":owner,"task_id":task_id,"status":status,
              "kind":"scheduled","summary":summary[:11000]
            }
            # Store only individual user's output. Never print private content.
            try:
                saved=self.db("enna_clone_runs","POST",record)
                run_id=saved[0]["id"] if saved else None
                # Owner-controlled feature gate; suggests revisions, not code changes.
                enabled=self.db("enna_clone_feature_flags?select=enabled,audience&feature=eq.proactive_suggestions&limit=1")
                if status=="complete" and enabled and enabled[0].get("enabled") and enabled[0].get("audience")!="closed":
                    # A separate billed AI call is explicitly quota-gated.
                    # No automatic edits, online browsing or permissions change.
                    extra=self.db("rpc/enna_clone_reserve_request","POST",{
                        "p_owner":owner,"p_daily_limit":4,"p_global_limit":40
                    })
                    if extra is True:
                        try:
                            suggestion=self.model_reply(
                                "Bạn đang giúp một người dùng cải tiến QUY TRÌNH, không được sửa mã "
                                "hoặc tự thực hiện việc gì. Từ tác vụ: "+
                                prompt[:700]+"; và kết quả nháp: "+summary[:1000]+
                                ". Đề xuất HAI cải tiến thực dụng và RIÊNG cho tình huống này, "
                                "mỗi ý nêu vì sao và cách kiểm chứng. "
                                "Viết tối đa 180 từ tiếng Việt, không lời khuyên sáo rỗng, "
                                "không tự bịa dữ kiện, không xin quyền truy cập mới.")
                            self.db("enna_clone_suggestions","POST",{
                                "owner_id":owner,"run_id":run_id,
                                "suggestion":suggestion[:1000],"status":"pending"
                            })
                        except (HTTPError,URLError,OSError,ValueError,RuntimeError,KeyError,IndexError):
                            pass  # Completed task remains complete, no repeated retries.

            except (HTTPError,URLError,OSError,ValueError,KeyError,IndexError):
                status="failed" # Fail closed, no secret or private message in console.
            results.append({"status":status,"task_processed":True})
        return results

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--dry-run",action="store_true",
                        help="Validate safety bounds without database or AI calls")
    a=parser.parse_args(argv)
    if a.dry_run:
        assert MAX_CLAIM<=4 and MAX_REPLY_TOKENS<=1000
        print("Enna Clone worker dry-run: no network, no task writes")
        return 0
    if os.getenv("CLONE_WORKER_ENABLED","false").lower()!="true":
        print("Enna Clone worker disabled until controlled update; no tasks processed.")
        return 0
    try:
        results=CloneWorker().run_once()
        print(json.dumps({"claimed":len(results),
                          "completed":sum(r["status"]=="complete" for r in results),
                          "failed":sum(r["status"]=="failed" for r in results),
                          "skipped":sum(r["status"]=="skipped" for r in results)}))
        return 0
    except (HTTPError,URLError,OSError,ValueError,RuntimeError):
        print("Enna Clone worker unavailable; no private information shown.")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
