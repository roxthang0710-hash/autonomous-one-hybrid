"""E3 regression: fail-safe adaptive provider choice, no endless retries."""
import unittest
from datetime import datetime, timedelta, timezone

from growth.agent_failure_reflection import classify, AUTH_BLOCKERS
from growth.agent_goal_cycle import build_proposals
from growth.agent_decision_policy import choose

NOW = datetime(2026, 11, 6, 18, 0, tzinfo=timezone.utc)
PERMS = {"threads_read", "threads_insights"}


def at(hours=0):
    return (NOW - timedelta(hours=hours)).isoformat()


def failure(action, code, hours=1, status="blocked"):
    return {"selected_action": action, "result_code": code,
            "status": status, "finished_at": at(hours)}


def evidence(feed_hours=14, followers_hours=20):
    return (
        [{"source": "meta_official", "measured_at": at(followers_hours)}],
        [{"source": "meta_official", "last_observed_at": at(feed_hours)}],
    )


class AgentFailureReflectionTests(unittest.TestCase):
    def test_missing_owner_oauth_blocks_requery(self):
        f = failure("refresh_official_meta_feed", "meta_owner_oauth_unavailable")
        decision = classify([f], action=f["selected_action"], observed_at=at(18), now=NOW)
        self.assertFalse(decision["allow"])
        self.assertEqual(decision["requires"], "owner_reconnect_or_independent_proof")

    def test_hard_scope_issue_blocks_only_affected_tool(self):
        followers, feed = evidence()
        history = [failure("refresh_official_followers",
                           "missing_threads_manage_insights_or_unavailable", 1)]
        proposals = build_proposals(followers, feed, history, NOW)
        self.assertEqual([x["action"] for x in proposals],
                         ["refresh_official_meta_feed"])

    def test_real_fallback_to_second_action_without_social_post(self):
        followers, feed = evidence()
        history = [failure("refresh_official_meta_feed",
                           "meta_owner_oauth_unavailable", 1)]
        decision = choose(build_proposals(followers, feed, history, NOW),
                          now=NOW, permissions=PERMS)
        self.assertEqual(decision["selected"]["action"],
                         "refresh_official_followers")
        self.assertIs(decision["external_social_writes_allowed"], False)

    def test_unverified_storage_readback_requires_different_diagnosis(self):
        info = classify([failure("refresh_official_meta_feed",
                 "provider_saved_but_source_readback_missing",2, "unverified")],
                 action="refresh_official_meta_feed", observed_at=at(18), now=NOW)
        self.assertEqual(info["requires"], "diagnose_private_storage_before_requery")
        self.assertFalse(info["allow"])

    def test_readback_soft_pause_expires(self):
        info = classify([failure("refresh_official_meta_feed",
              "provider_saved_but_source_readback_missing", 13, "unverified")],
              action="refresh_official_meta_feed", observed_at=at(18), now=NOW)
        self.assertTrue(info["allow"])

    def test_hard_permission_pause_expires_but_normal_guard_still_applies(self):
        info = classify([failure("refresh_official_followers",
              "identity_mismatch", 74)],
              action="refresh_official_followers", observed_at=at(80), now=NOW)
        self.assertTrue(info["allow"])
        self.assertEqual(info["requires"], "normal_policy_gate")

    def test_new_official_evidence_overrides_old_failure_cautiously(self):
        info = classify([failure("refresh_official_meta_feed",
              "meta_owner_oauth_unavailable", 3)],
              action="refresh_official_meta_feed",
              observed_at=at(1), now=NOW)
        self.assertTrue(info["allow"])
        self.assertEqual(info["reason"], "official_source_newer_than_failure")

    def test_legacy_missing_result_code_preserves_existing_behavior(self):
        old = {"selected_action":"refresh_official_meta_feed",
               "status":"blocked", "finished_at":at(3)}
        info = classify([old], action="refresh_official_meta_feed",
                        observed_at=at(15), now=NOW)
        self.assertTrue(info["allow"])

    def test_missing_failure_timestamp_fails_closed(self):
        bad = {"selected_action":"refresh_official_meta_feed",
               "status":"blocked","result_code":"meta_owner_oauth_unavailable"}
        info = classify([bad], action="refresh_official_meta_feed",
                        observed_at=at(15), now=NOW)
        self.assertFalse(info["allow"])
        self.assertEqual(info["reason"], "previous_failure_time_unverified")

    def test_history_order_is_not_assumed(self):
        old = failure("refresh_official_meta_feed","identity_mismatch", 48)
        new = failure("refresh_official_meta_feed","provider_error", 1)
        info = classify([new,old], action="refresh_official_meta_feed",
                        observed_at=at(50),now=NOW)
        self.assertFalse(info["allow"])

    def test_no_cross_tool_block_for_insufficient_source(self):
        f = failure("refresh_official_meta_feed","meta_owner_oauth_unavailable")
        info = classify([f],action="refresh_official_followers",
                        observed_at=at(14),now=NOW)
        self.assertTrue(info["allow"])

    def test_unknown_tool_cannot_be_unblocked_by_memory(self):
        info = classify([failure("publish_social_post","identity_mismatch")],
                        action="publish_social_post",
                        observed_at=at(18), now=NOW)
        self.assertFalse(info["allow"])
        self.assertNotIn("token",str(info).lower())

    def test_proposals_reflect_history_not_a_fabricated_approval(self):
        followers, feed = evidence()
        history = [failure("refresh_official_meta_feed",
                           "meta_owner_oauth_unavailable", 1),
                   failure("refresh_official_followers",
                           "missing_threads_manage_insights_or_unavailable", 1)]
        proposed = build_proposals(followers, feed, history, NOW)
        self.assertEqual(proposed, [])
        actual = choose(proposed, now=NOW, permissions=PERMS)
        self.assertIsNone(actual["selected"])

    def test_history_bounded(self):
        with self.assertRaises(ValueError):
            classify([{}]*101, action="refresh_official_meta_feed",
                     observed_at=at(18),now=NOW)

    def test_all_known_oauth_failures_are_scoped(self):
        self.assertIn("identity_mismatch",AUTH_BLOCKERS)
        self.assertIn("missing_threads_manage_insights_or_unavailable",AUTH_BLOCKERS)


if __name__ == "__main__":
    unittest.main()
