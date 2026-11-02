import unittest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta
from growth.diagnostic import inspect

NOW=datetime(2026,11,2,13,0,tzinfo=timezone.utc)
SELF={"username":"dohay_dilam","text":"Mẹo hay cho dân văn phòng. Sống gọn hơn.",
      "timestamp":(NOW-timedelta(hours=1)).isoformat()}
OTHER={"username":"writer","text":"Góc bàn làm việc laptop công sở gọn gàng",
       "timestamp":(NOW-timedelta(hours=1)).isoformat()}
class DiagnosticTests(unittest.TestCase):
    def test_detect_own_only(self):
        def fetch(*a,**k):
            r=Mock();r.json.return_value={"data":[SELF]};return r
        data=inspect("fake",fetch=fetch,now=NOW)
        self.assertEqual(data["result"],"own_only_possible_app_review")
        self.assertTrue(all(t["foreign"]==0 for t in data["tests"]))
    def test_confirm_actual_external(self):
        def fetch(*a,**k):
            r=Mock();r.json.return_value={"data":[OTHER]};return r
        data=inspect("fake",fetch=fetch,now=NOW)
        self.assertEqual(data["result"],"external_posts_present")
    def test_empty_never_means_viral_posts_do_not_exist(self):
        def fetch(*a,**k):
            r=Mock();r.json.return_value={"data":[]};return r
        self.assertEqual(inspect("fake",fetch=fetch,now=NOW)["result"],
                         "empty_raw_results_cause_unconfirmed")
    def test_all_requests_read_only(self):
        seen=[]
        def fetch(*a,**k):
            seen.append(k)
            r=Mock();r.json.return_value={"data":[]};return r
        inspect("fake",fetch=fetch,now=NOW)
        self.assertEqual(len(seen),4)
        self.assertEqual(seen[-1]["params"]["search_mode"],"TAG")
        self.assertTrue(all("q" in x["params"] for x in seen))
if __name__=="__main__": unittest.main()
