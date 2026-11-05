"""Pre-release protection for the standalone Enna Clone multi-user cloud beta."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT=Path(__file__).resolve().parents[1]
CODE=ROOT/"supabase/functions/enna-clone-api/index.ts"
FRONT=ROOT/"docs/enna/clone/beta/index.html"
JS=ROOT/"docs/enna/clone/beta/app.js"
WORKER=ROOT/"growth/enna_clone_worker.py"
WORKFLOW=ROOT/".github/workflows/enna-clone-personal-jobs.yml"

def load_worker():
    spec=importlib.util.spec_from_file_location("enna_clone_worker",WORKER)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class CloudCloneSafetyTests(unittest.TestCase):
    def test_backend_uses_verified_identity_and_owner_scoping(self):
        code=CODE.read_text(encoding="utf-8")
        self.assertIn('"/auth/v1/user"',code)
        self.assertIn("enna_clone_beta_access",code)
        self.assertIn("owner_id=eq.",code)
        self.assertIn("enna_clone_reserve_request",code)
        self.assertIn("p_daily_limit:4",code)
        self.assertIn("p_global_limit:40",code)
        self.assertIn('await assertFeature(owner,"live_chat")',code)
        self.assertIn("conversation_id=eq.",code)
        self.assertIn('request_id=eq.',code)
        self.assertIn('role:"assistant"',code)
        self.assertIn("Không có công cụ gửi email",code)
        self.assertNotIn("THREADS_APP_SECRET",code)
        self.assertNotIn("THREADS_TOKEN_KEY",code)
        self.assertNotIn("THREADS_PUBLISH_ENABLED",code)

    def test_frontend_keys_and_no_html_injection(self):
        html=FRONT.read_text(encoding="utf-8")
        js=JS.read_text(encoding="utf-8")
        self.assertIn("app.js",html)
        self.assertIn("script-src 'self'",html)
        self.assertIn("connect-src https://gjdvdohylvsauphhkutw.supabase.co",html)
        self.assertIn("sb_publishable_",js)
        self.assertIn('sessionStorage',js)
        self.assertIn(".textContent=",js)
        self.assertNotIn("innerHTML",js)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",js)
        self.assertNotIn("DB_SERVICE_KEY",js)
        self.assertNotIn("GROQ_API_KEY",js)
        self.assertNotIn("x-api-key",html.lower())
        self.assertNotIn("<script src='http",html)
        self.assertIn("PRIVATE BETA",html)

    def test_worker_has_no_social_access_or_unbounded_proposals(self):
        src=WORKER.read_text(encoding="utf-8")
        flow=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("enna_clone_claim_due",src)
        self.assertIn("enna_clone_reserve_request",src)
        self.assertIn("enna_clone_runs",src)
        self.assertIn("enna_clone_suggestions",src)
        self.assertIn("MAX_CLAIM=4",src)
        self.assertIn("MAX_REPLY_TOKENS=850",src)
        self.assertNotIn("THREADS_TOKEN",src)
        self.assertNotIn("Metricool",src)
        self.assertNotIn("subprocess",src)
        self.assertNotIn("while True",src)
        self.assertIn("concurrency:",flow)
        self.assertIn("CLONE_WORKER_ENABLED: 'true'",flow)
        self.assertNotIn("THREADS_APP_SECRET",flow)

    def test_offline_dry_run_uses_no_secrets(self):
        worker=load_worker()
        with patch.dict(worker.os.environ,{},clear=True):
            self.assertEqual(worker.main(["--dry-run"]),0)
            self.assertEqual(worker.main([]),0)

    def test_jobs_generate_one_record_per_bounded_claim(self):
        worker=load_worker()
        fake=worker.CloneWorker(url="https://example.supabase.co",
                                service_key="FAKE_TEST",
                                groq_key="FAKE_GROQ")
        calls=[]
        def pretend(path,method="GET",body=None):
            calls.append((path,method,body))
            if path=="rpc/enna_clone_claim_due":
                return [{"id":"fake-task","owner_id":"fake-owner",
                         "instruction":"Tạo một bản nháp giả lập."}]
            if path=="rpc/enna_clone_reserve_request": return True
            if path=="enna_clone_runs":return [{"id":"fake-run"}]
            if path.startswith("enna_clone_feature_flags"):return [{"enabled":False,"audience":"closed"}]
            raise AssertionError("Unexpected access: "+path)
        with patch.object(fake,"db",side_effect=pretend),patch.object(fake,"model_reply",return_value="Bản mẫu"):
            results=fake.run_once()
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]["status"],"complete")
        self.assertEqual(len([x for x in calls if x[0]=="rpc/enna_clone_reserve_request"]),1)
        self.assertEqual(len([x for x in calls if x[0]=="enna_clone_runs"]),1)
        self.assertFalse(any(x[0]=="enna_clone_suggestions" for x in calls))

if __name__=="__main__":
    unittest.main()
