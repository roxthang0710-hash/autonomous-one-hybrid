import unittest
from planner import choose_topic, should_pause_scheduled, DEFAULT_TOPICS


class PlannerTests(unittest.TestCase):
    def test_first_topic(self):
        self.assertEqual(choose_topic([]), DEFAULT_TOPICS[0])

    def test_rotate_to_least_covered(self):
        self.assertEqual(choose_topic([
            {"topic": DEFAULT_TOPICS[0], "approval_status": "pending"},
        ]), DEFAULT_TOPICS[1])

    def test_pause_when_queue_is_full(self):
        history = [{"approval_status": "pending"}] * 8
        self.assertTrue(should_pause_scheduled(history))
        self.assertFalse(should_pause_scheduled(history[:7]))

    def test_approved_feedback_opens_capacity(self):
        history = [{"approval_status": "pending"}] * 7
        history.append({"approval_status": "approved"})
        self.assertFalse(should_pause_scheduled(history))


if __name__ == "__main__":
    unittest.main()
