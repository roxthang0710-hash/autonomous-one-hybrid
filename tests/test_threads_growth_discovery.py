"""No-network tests for official Threads keyword discovery and trend priority."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from growth.conversations import search_threads, QUERIES
from growth.runner import build_candidates

NOW = datetime(2026, 11, 2, 7, 20, tzinfo=timezone.utc)
VALID_TEXT = "Bàn làm việc laptop văn phòng bừa bộn quá, mọi người sắp xếp sao?"
POST = {
    "id": "999123", "text": VALID_TEXT, "username": "real_thread_user",
    "permalink": "https://www.threads.com/@real_thread_user/post/abc",
    "timestamp": (NOW-timedelta(hours=2)).isoformat(),
}

class ConversationDiscoveryTests(unittest.TestCase):
    def test_only_one_authorized_api_query_for_top_recent_discovery(self):
        calls = []
        def fetch(url, **kwargs):
            calls.append((url,kwargs))
            r=Mock()
            r.json.return_value={"data":[POST]}
            r.raise_for_status.return_value=None
            return r
        with patch.dict("os.environ",{"THREADS_DISCOVERY_ENABLED":"true"}):
            rows,status=search_threads(
                query="bàn làm việc",fetch=fetch,token="mock-token",
                search_type="TOP",now=NOW)
        self.assertEqual(status,"ok")
        self.assertEqual(len(rows),1)
        self.assertEqual(calls[0][1]["params"]["search_type"],"TOP")
        self.assertEqual(calls[0][1]["headers"]["Authorization"],"Bearer mock-token")

    def test_skip_brand_self_and_stale_unrelated_or_sensitive_posts(self):
        records=[
            POST,
            dict(POST,id="self",username="dohay_dilam"),
            dict(POST,id="old",timestamp=(NOW-timedelta(hours=40)).isoformat()),
            dict(POST,id="political",text="Bầu cử, chính trị và chiến tranh tại văn phòng"),
            dict(POST,id="offbrand",text="Nấu canh ngọt và xem bóng đá buổi tối")
        ]
        def fetch(url,**kwargs):
            r=Mock();r.json.return_value={"data":records};return r
        with patch.dict("os.environ",{"THREADS_DISCOVERY_ENABLED":"true"}):
            rows,status=search_threads(
                query="bàn làm việc",fetch=fetch,token="mock-token",now=NOW)
        self.assertEqual([r["id"] for r in rows],["999123"])

    def test_self_only_results_flag_app_review_risk(self):
        def fetch(url,**kwargs):
            r=Mock()
            r.json.return_value={"data":[dict(POST,username="dohay_dilam")]}
            r.raise_for_status.return_value=None
            return r
        with patch.dict("os.environ",{"THREADS_DISCOVERY_ENABLED":"true"}):
            rows,status=search_threads(
                query="bàn làm việc",fetch=fetch,token="fake-test",
                now=NOW)
        self.assertEqual(rows,[])
        self.assertEqual(status,"own_posts_only_possible_app_review")

    def test_empty_search_is_not_called_successful_public_discovery(self):
        def fetch(url,**kwargs):
            r=Mock()
            r.json.return_value={"data":[]}
            r.raise_for_status.return_value=None
            return r
        with patch.dict("os.environ",{"THREADS_DISCOVERY_ENABLED":"true"}):
            rows,status=search_threads(
                query="bàn làm việc",fetch=fetch,token="fake-test",
                now=NOW)
        self.assertEqual(rows,[])
        self.assertEqual(status,"empty_keyword_results")

    def test_threads_source_not_hidden_by_fourteen_google_titles(self):
        rss=[{
            "title": "Laptop văn phòng và bàn làm việc, 10 cách sắp xếp",
            "source":"google_news_vn",
            "source_url":"https://news.google.com/rss/articles/"+str(i),
            "fingerprint":"rss_"+str(i),"published_at":NOW
        } for i in range(20)]
        threads=[{
            "title":"Bàn làm việc nhỏ rất khó dọn dẹp",
            "id":"threads_original_1",
            "url":"https://www.threads.com/@poster/post/z",
            "username":"poster",
            "published_at":NOW-timedelta(hours=1),
        }]
        rows=build_candidates(rss,threads,now=NOW)
        self.assertEqual(len(rows),14)
        self.assertEqual(sum(r["source"]=="threads_keyword_api" for r in rows),1)


if __name__=="__main__":
    unittest.main()
