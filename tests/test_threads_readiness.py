import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from threads.readiness import snapshot

NOW = datetime(2026, 11, 2, 8, 30, tzinfo=timezone.utc)
BRAND = {
    "brand_key": "do_hay_di_lam", "status": "connected",
    "authorized": True, "auto_publish_enabled": True,
    "account_created_at": None, "shopee_channel_approved": False,
}
POSTS = [
    {"status":"scheduled_external", "scheduled_at":"2026-11-03T02:30:00+00:00",
     "published_at":None},
    {"status":"scheduled_external", "scheduled_at":"2026-11-17T02:30:00+00:00",
     "published_at":None},
    {"status":"queued", "scheduled_at":"2026-11-18T02:30:00+00:00",
     "published_at":None},
]


def prepared_db(posts=POSTS, credential=None, measurements=None):
    db = MagicMock()
    cred = credential if credential is not None else [
        {"status":"active","expires_at":"2027-01-01T09:15:00+00:00"}]
    metrics = measurements if measurements is not None else []
    def request(method,path,**kwargs):
        if path == "/threads_channels": return [BRAND]
        if path == "/threads_posts": return posts
        if path == "/threads_metrics": return metrics
        if path == "/threads_vault_credentials": return cred
        raise AssertionError("Unexpected query " + path)
    db.request.side_effect = request
    return db


class ReadinessTests(unittest.TestCase):
    def test_cultivation_never_claims_shopee_approval_or_sales(self):
        actual = snapshot(prepared_db(), now=NOW)
        self.assertEqual(actual["status"], "connected")
        self.assertEqual(actual["threads_posts"]["scheduled_external"], 2)
        self.assertEqual(actual["threads_posts"]["queued"], 1)
        self.assertEqual(actual["threads_posts"]["posted"], 0)
        self.assertEqual(actual["next_queued_local_date"], "2026-11-18")
        self.assertEqual(actual["shopee_affiliate"]["channel_approval"],
                         "not_yet_approved")
        self.assertEqual(actual["shopee_affiliate"]["revenue"], "not_measured")
        self.assertFalse(actual["measured_insights_available"])
        self.assertIsNone(actual["account_age_days_if_recorded"])
        self.assertEqual(actual["warnings"], [])

    def test_duplicated_booking_day_is_reported_not_published(self):
        posts = POSTS + [
            {"status":"queued","scheduled_at":"2026-11-17T09:45:00+00:00",
             "published_at":None}
        ]
        actual=snapshot(prepared_db(posts=posts),now=NOW)
        self.assertIn("potential_metricool_conflicting_dates",actual["warnings"])

    def test_oauth_missing_and_uncertain_post_are_flagged(self):
        posts = POSTS + [
            {"status":"uncertain","scheduled_at":"2026-11-01T02:30:00+00:00",
             "published_at":None}
        ]
        actual=snapshot(prepared_db(posts=posts,credential=[]),now=NOW)
        self.assertIn("no_valid_oauth_token",actual["warnings"])
        self.assertIn("uncertain_publication_requires_reconciliation",actual["warnings"])
        self.assertEqual(actual["status"], "connection_attention_needed")


if __name__ == "__main__":
    unittest.main()
