import unittest
from unittest.mock import MagicMock, patch
from threads.insights import parse_insights, collect


class InsightsTests(unittest.TestCase):
    def test_official_response_parses_valid_metrics(self):
        data = {"data": [
            {"name": "views", "values": [{"value": 10}]},
            {"name": "likes", "values": [{"value": 3}]},
            {"name": "replies", "values": [{"value": 2}]},
            {"name": "reposts", "values": [{"value": 1}]},
            {"name": "quotes", "values": [{"value": 0}]},
        ]}
        self.assertEqual(parse_insights(data),
                         {"views": 10, "likes": 3, "replies": 2, "reposts": 1, "quotes": 0})

    def test_unreturned_not_invented(self):
        data = {"data": [{"name": "likes", "values": [{"value": 2}]}]}
        x = parse_insights(data)
        self.assertEqual(x, {"likes": 2})
        self.assertNotIn("views", x)

    def test_meta_total_value_is_a_real_measurement(self):
        payload={"data":[
            {"name":"views","total_value":{"value":18}},
            {"name":"replies","values":[{"value":0}]},
        ]}
        self.assertEqual(parse_insights(payload),{"views":18,"replies":0})

    def test_partial_real_metrics_are_saved_without_guessing_zeros(self):
        db=MagicMock()
        db.request.return_value=[{"id":"one","platform_post_id":"meta123"}]
        with patch("threads.credentials.load_credentials",return_value=("token","dohay_dilam")), \
             patch("threads.insights.authenticate"), \
             patch("threads.insights.get_channel",return_value={"id":"brand"}), \
             patch("threads.insights.thread_request",return_value={"data":[
                 {"name":"views","values":[{"value":78}]},
                 {"name":"likes","total_value":{"value":5}},
             ]}):
            self.assertEqual(collect(db),"snapshots_saved:1")
        row=db.insert.call_args.args[1]
        self.assertEqual(row["post_id"],"one")
        self.assertEqual(row["views"],78)
        self.assertEqual(row["likes"],5)
        self.assertNotIn("replies",row)
        self.assertNotIn("quotes",row)

    def test_disconnected_account_skips(self):
        db = MagicMock()
        with patch("threads.credentials.load_credentials", return_value=None):
            self.assertEqual(collect(db), "waiting_for_owner_oauth_and_enable_switch")
        db.request.assert_not_called()

    def test_no_posts_no_fabricated_insights(self):
        db = MagicMock()
        db.request.return_value = []
        with patch("threads.credentials.load_credentials", return_value=("token", "brand")), \
             patch("threads.insights.authenticate"), \
             patch("threads.insights.get_channel", return_value={"id": "channel"}):
            self.assertEqual(collect(db), "no_published_posts")
        db.insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
