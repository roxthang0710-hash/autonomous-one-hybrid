import unittest
from unittest.mock import Mock
from agent import queue_owner_issue


class EventQueueTests(unittest.TestCase):
    def test_issue_is_durably_queued(self):
        db = Mock()
        queue_owner_issue(db, "42", "marketing automation")
        method, path = db.request.call_args.args[:2]
        self.assertEqual((method, path), ("POST", "/agent_events"))
        fields = db.request.call_args.kwargs
        self.assertEqual(fields["payload"]["request_id"], "github-issue-42")
        self.assertEqual(fields["payload"]["kind"], "research_request")
        self.assertEqual(fields["payload"]["payload"]["topic"], "marketing automation")

    def test_issue_duplicate_upsert_is_ignored(self):
        db = Mock()
        queue_owner_issue(db, "42", "marketing automation")
        self.assertIn("ignore-duplicates", db.request.call_args.kwargs["prefer"])

    def test_empty_issue_is_not_queued(self):
        db = Mock()
        queue_owner_issue(db, "", "")
        db.request.assert_not_called()

    def test_invalid_issue_is_rejected(self):
        with self.assertRaises(ValueError):
            queue_owner_issue(Mock(), "oops", "marketing automation")


if __name__ == "__main__":
    unittest.main()
