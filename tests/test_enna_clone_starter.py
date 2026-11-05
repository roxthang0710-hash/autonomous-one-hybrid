"""Safety and utility tests for the publicly shareable Enna Clone Starter."""
import importlib.util
import io
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
import tempfile
import unittest

PATH=Path(__file__).resolve().parents[1]/"starter"/"enna-clone"/"agent.py"
spec=importlib.util.spec_from_file_location("enna_clone_starter",PATH)
clone=importlib.util.module_from_spec(spec)
spec.loader.exec_module(clone)

class PublicCloneStarterTests(unittest.TestCase):
    def test_offline_demo_has_no_api_key_or_network_access(self):
        with patch.object(clone,"request_model",side_effect=AssertionError("must not call API")):
            output=io.StringIO()
            with redirect_stdout(output):
                status=clone.main(["--demo","--mode","meeting"])
            self.assertEqual(status,0)
            self.assertIn("KHÔNG GỌI AI",output.getvalue())
            self.assertIn("Chưa có bất kỳ mô hình",output.getvalue())

    def test_task_bounded_with_no_unintended_file_access(self):
        self.assertRaises(ValueError,clone.user_request,"meeting","")
        self.assertRaises(ValueError,clone.user_request,"email","x"*9001)
        self.assertRaises(ValueError,clone.user_request,"dangerous","hello")
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"private.txt"
            p.write_text("Mẫu cuộc họp không có dữ liệu nhạy cảm",encoding="utf-8")
            self.assertIn("cuộc họp",clone.load_context(str(p)))
            with self.assertRaises(ValueError):
                clone.load_context(str(Path(folder)/"missing.txt"))
            p.write_text("A"*10001,encoding="utf-8")
            with self.assertRaises(ValueError):
                clone.load_context(str(p))

    def test_system_boundaries_are_explicit_and_untrusted_input_wrapped(self):
        self.assertIn("không có quyền đọc email",clone.SYSTEM)
        self.assertIn("Không thực thi",clone.SYSTEM)
        self.assertIn("<<<BEGIN_USER_DATA>>>",
                      clone.user_request("meeting","Làm bảng","Tài liệu thử"))
        self.assertIn("DỰ THẢO",clone.SYSTEM)

    def test_two_model_calls_max_and_human_review(self):
        calls=[]
        def fake(messages, *,api_key,model):
            calls.append(messages)
            self.assertEqual(api_key,"FAKE_TEST_ONLY_NOT_A_SECRET")
            return "Bản nháp cần người duyệt" if len(calls)==1 else "Bản kiểm đã rà soát"
        with patch.object(clone,"request_model",side_effect=fake):
            result=clone.run("meeting","Tóm tắt ghi chú", "Bản giả lập",
                             api_key="FAKE_TEST_ONLY_NOT_A_SECRET",model=clone.DEFAULT_MODEL)
        self.assertEqual(len(calls),2)
        self.assertEqual(len(calls[0]),2)
        self.assertEqual(len(calls[1]),4)
        self.assertIn("DỰ THẢO",result)
        self.assertIn("Chưa có email, file, lịch",result)

    def test_missing_key_fails_without_exposing_sensitive_text(self):
        error=io.StringIO()
        with patch.dict(clone.os.environ,{},clear=True),redirect_stderr(error):
            result=clone.main(["--mode","email","--task","Soạn lời nhắc lịch"])
        self.assertEqual(result,2)
        self.assertIn("Không hoàn thành",error.getvalue())
        self.assertNotIn("Soạn lời nhắc lịch",error.getvalue())

    def test_fixed_api_and_no_command_execution(self):
        source=PATH.read_text(encoding="utf-8")
        self.assertEqual(clone.ENDPOINT,"https://api.groq.com/openai/v1/chat/completions")
        for forbidden in ("subprocess", "eval(", "exec(", "shell=True", "os.system(", "localhost"):
            self.assertNotIn(forbidden,source)
        self.assertEqual(clone.MAX_OUTPUT_TOKENS,1000)
        self.assertLessEqual(clone.REQUEST_TIMEOUT,30)

if __name__=="__main__":
    unittest.main()
