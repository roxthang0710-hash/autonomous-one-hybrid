"""Daily loop should plan and publish independently, with one publisher only."""
import unittest
from unittest.mock import MagicMock, patch

from threads.daily import daily


class DailyLoopTests(unittest.TestCase):
    def test_no_meta_token_causes_no_public_action(self):
        db = MagicMock()
        with patch("threads.daily.seed_calendar", return_value=0), \
             patch("threads.daily.plan_next", return_value="sufficient_backlog"), \
             patch("threads.daily.publish_due", return_value=
                   "waiting_for_owner_oauth_and_enable_switch") as pub, \
             patch("threads.daily.collect", return_value=
                   "waiting_for_owner_oauth_and_enable_switch"):
            r = daily(db)
        self.assertEqual(r["publisher"], "waiting_for_owner_oauth_and_enable_switch")
        pub.assert_called_once_with(db)

    def test_groq_failure_never_cancels_preapproved_publication(self):
        db = MagicMock()
        with patch("threads.daily.seed_calendar", return_value=0), \
             patch("threads.daily.plan_next", side_effect=RuntimeError("model down")), \
             patch("threads.daily.publish_due", return_value="published") as pub, \
             patch("threads.daily.collect", return_value="no_published_posts"):
            r = daily(db)
        self.assertEqual(r["publisher"], "published")
        self.assertIn("error:RuntimeError", r["editor"])
        pub.assert_called_once_with(db)

    def test_manual_planning_is_never_a_publishing_action(self):
        db = MagicMock()
        with patch("threads.daily.seed_calendar", return_value=0), \
             patch("threads.daily.plan_next", return_value="sufficient_backlog"), \
             patch("threads.daily.publish_due") as pub:
            r = daily(db, publish=False, metrics=False)
        self.assertEqual(r["publisher"], "disabled_for_manual_planning")
        pub.assert_not_called()


if __name__ == "__main__":
    unittest.main()
