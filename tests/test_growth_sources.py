import unittest
from unittest.mock import Mock
from growth.sources import read_rss, discover
from growth.conversations import can_search, search_threads
from unittest.mock import patch

SAMPLE = b"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>VN Trends</title>
<item><title>Meo du lich hanh ly gon nhe</title>
<link>https://trends.google.com/trending?geo=VN</link>
<pubDate>Mon, 02 Nov 2026 03:00:00 GMT</pubDate></item>
<item><title>Xu huong ban lam viec</title>
<link>https://trends.google.com/trending?geo=VN</link></item>
</channel></rss>"""


class GrowthSourcesTests(unittest.TestCase):
    def test_rss_is_parseable_without_external_network(self):
        a = read_rss(SAMPLE, "google_trends_vn")
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0]["source"], "google_trends_vn")
        self.assertIsNotNone(a[0]["published_at"])

    def test_reject_dtd(self):
        with self.assertRaises(ValueError):
            read_rss(b'<!DOCTYPE a><rss version="2.0"/>', "google_trends_vn")

    def test_failure_is_reported_not_fabricated(self):
        def fails(url, headers, timeout):
            raise ValueError("Unavailable")
        rows, summary = discover(fetch=fails)
        self.assertEqual(rows, [])
        self.assertTrue(any(x == "ValueError" for x in summary.values()))

    def test_threads_discovery_off_has_no_network_calls(self):
        with patch.dict("os.environ", {
                "THREADS_DISCOVERY_ENABLED": "false",
                "THREADS_DISCOVERY_ACCESS_TOKEN": "fake"}):
            self.assertFalse(can_search())
            fetch = Mock()
            rows, outcome = search_threads(fetch=fetch)
            self.assertEqual((rows, outcome), ([], "not_authorized"))
            fetch.assert_not_called()

    def test_threads_only_allowlisted_queries(self):
        with patch.dict("os.environ", {
                "THREADS_DISCOVERY_ENABLED": "true",
                "THREADS_DISCOVERY_ACCESS_TOKEN": "fake"}):
            fetch = Mock()
            rows, outcome = search_threads(query="celebrity scandal", fetch=fetch)
            self.assertEqual(outcome, "disallowed_query")
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
