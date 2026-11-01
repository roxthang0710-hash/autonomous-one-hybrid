import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from threads.reconcile import find_matches, reconcile

NOW = datetime(2026, 11, 4, 10, tzinfo=timezone.utc)
TEXT = "Sắp xếp bàn làm việc thế nào để người đi làm tập trung hơn?"


def draft():
    return {"id": "p1", "scheduled_at": "2026-11-03T02:30:00+00:00",
            "text_content": TEXT}


def meta(text=TEXT, timestamp="2026-11-03T02:30:03+0000"):
    return {"id": "meta123", "text": text, "timestamp": timestamp,
            "permalink": "https://www.threads.com/@dohay_dilam/post/test"}


class ReconciliationTests(unittest.TestCase):
    def test_exact_match_proves_real_publication(self):
        rows = find_matches([draft()], [meta()])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["platform_post_id"], "meta123")

    def test_not_matching_the_same_text_is_not_evidence(self):
        self.assertEqual(find_matches([draft()], [meta(text="Another post")]), [])

    def test_posts_far_from_expected_day_are_not_claimed(self):
        self.assertEqual(find_matches([draft()], [
            meta(timestamp="2026-10-30T02:30:03+0000")]), [])

    def test_duplicate_meta_matches_are_ambiguous(self):
        duplicate = dict(meta(), id="meta999")
        self.assertEqual(find_matches([draft()], [meta(),duplicate]), [])

    def test_no_token_no_real_world_call(self):
        db = MagicMock()
        with patch("threads.reconcile.load_credentials", return_value=None), \
             patch("threads.reconcile.thread_request") as api:
            self.assertEqual(reconcile(db), "waiting_for_owner_meta_oauth")
        api.assert_not_called()

    def test_metricool_pending_is_not_mistaken_for_published(self):
        db = MagicMock()
        db.request.return_value = [draft()]
        with patch("threads.reconcile.load_credentials",
                   return_value=("token", "dohay_dilam")), \
             patch("threads.reconcile.authenticate"), \
             patch("threads.reconcile.thread_request",
                   return_value={"data": [meta(text="Not the same text")]}):
            self.assertEqual(reconcile(db, now=NOW), "confirmed_metricool_posts:0")
        self.assertFalse(any(c.args[0]=="PATCH" for c in db.request.call_args_list))

    def test_proven_meta_post_is_saved_once(self):
        db = MagicMock()
        db.request.side_effect = [[draft()], [{"id": "p1"}]]
        with patch("threads.reconcile.load_credentials",
                   return_value=("token", "dohay_dilam")), \
             patch("threads.reconcile.authenticate"), \
             patch("threads.reconcile.thread_request",
                   return_value={"data": [meta()]}):
            self.assertEqual(reconcile(db, now=NOW), "confirmed_metricool_posts:1")
        patching = [c for c in db.request.call_args_list if c.args[0]=="PATCH"]
        self.assertEqual(patching[0].kwargs["payload"]["status"], "posted")
        self.assertEqual(patching[0].kwargs["payload"]["platform_post_id"],"meta123")


if __name__ == "__main__":
    unittest.main()
