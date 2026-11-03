import unittest
from unittest.mock import MagicMock
from growth.activity_log import emit

class ActivityAuditTests(unittest.TestCase):
    def test_fixed_codes_and_provider_safe_payload(self):
        db=MagicMock();db.request.return_value=[{"id":"x"}]
        emit(db,"publisher","started","ops_started",run_id="554433")
        args=db.request.call_args.kwargs
        payload=args["payload"]
        self.assertEqual(payload["dedup_key"],"github:554433:publisher:started:ops_started")
        self.assertEqual(payload["origin"],"github")
        self.assertNotIn("post_text",payload)
        self.assertNotIn("token",str(payload).lower())
    def test_reject_dynamic_log_text_and_fake_run(self):
        db=MagicMock()
        for code in ("raw_api_token:123","published:custom","Private customer text"):
            with self.assertRaises(ValueError):
                emit(db,"publisher","failed",code,run_id="55")
        with self.assertRaises(ValueError):
            emit(db,"publisher","started","ops_started",run_id="../")
        db.request.assert_not_called()

if __name__=="__main__":unittest.main()
