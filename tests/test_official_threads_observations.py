import hashlib
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import MagicMock

from growth.official_threads_observations import collect,parse_posts

NOW=datetime(2026,11,6,14,0,tzinfo=timezone.utc)
URL="https://www.threads.com/@dohay_dilam/post/DfY13eniC2X"

def post(ident="18123456789012345", text="Chuyện đi làm hài hước"):
    return {"id":ident,"timestamp":(NOW-timedelta(hours=1)).isoformat(),
            "text":text,"permalink":URL}

def reader(method,path,token,params=None):
    assert method=="GET" and token=="secret-test"
    if path=="/me":return {"username":"dohay_dilam","id":"thread-owner"}
    if path=="/me/threads":return {"data":[post()],"paging":{"next":"not-followed"}}
    raise AssertionError("Unexpected / Meta write request")

class ObservationsTests(unittest.TestCase):
    def test_validate_and_hash_without_saving_raw_text(self):
        r=parse_posts({"data":[post()]},now=NOW)[0]
        self.assertEqual(r["meta_post_id"],post()["id"])
        self.assertEqual(r["text_sha256"],hashlib.sha256(post()["text"].encode()).hexdigest())
        self.assertNotIn("text",r)
        self.assertEqual(r["permalink"],URL)

    def test_do_not_accept_bad_ids_urls_or_old_samples(self):
        bad=[post(ident="container-id"),
             {**post("18123456789012346"),"permalink":"https://phishing.example/p"},
             {**post("18123456789012347"),"timestamp":(NOW-timedelta(days=46)).isoformat()},
             {**post("18123456789012348"),"timestamp":(NOW+timedelta(days=1)).isoformat()},
             post()]
        found=parse_posts({"data":bad},now=NOW)
        self.assertEqual(len(found),2)
        self.assertIsNone(found[0]["permalink"])
        self.assertEqual(len({x["meta_post_id"] for x in found}),2)

    def test_missing_provider_data_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_posts({"message":"error"},now=NOW)

    def test_owner_oauth_required(self):
        db=MagicMock()
        result=collect(db,now=NOW,load=lambda db,refresh:None,read=reader)
        self.assertEqual(result["state"],"meta_owner_oauth_unavailable")
        db.request.assert_not_called()

    def test_identity_mismatch_blocks_publication_observation_write(self):
        def wrong(method,path,token,params=None):
            return {"username":"someone_else","id":"id"}
        db=MagicMock()
        result=collect(db,now=NOW,load=lambda db,refresh:("secret-test","dohay_dilam"),read=wrong)
        self.assertEqual(result["state"],"identity_unavailable")
        db.request.assert_not_called()

    def test_real_provider_read_plus_exact_db_readback(self):
        db=MagicMock()
        def route(method,path,params=None,payload=None,prefer=None):
            if method=="POST":
                self.assertEqual(path,"/enna_official_threads_observations")
                self.assertEqual(len(payload),1)
                self.assertNotIn("text",payload[0])
                return payload
            if method=="GET":
                self.assertEqual(path,"/enna_official_threads_observations")
                self.assertIn("18123456789012345",params["meta_post_id"])
                return [{"meta_post_id":"18123456789012345","source":"meta_official",
                         "published_at":post()["timestamp"]}]
            raise AssertionError("Unexpected database request")
        db.request.side_effect=route
        output=collect(db,now=NOW,load=lambda db,refresh:("secret-test","dohay_dilam"),read=reader)
        self.assertEqual(output["state"],"verified_official_feed")
        self.assertEqual(output["verified_count"],1)
        self.assertEqual(output["social_posts_created"],0)
        self.assertTrue(output["sample_paginated"])

    def test_upsert_does_not_prove_external_post(self):
        db=MagicMock()
        db.request.return_value=[]
        result=collect(db,now=NOW,load=lambda db,refresh:("secret-test","dohay_dilam"),read=reader)
        self.assertEqual(result["state"],"upsert_unverified")
        self.assertEqual(result["verified_count"],0)

    def test_db_wrong_readback_cannot_claim_verified(self):
        db=MagicMock()
        db.request.side_effect=lambda method,path,params=None,payload=None,prefer=None: (
            payload if method=="POST" else
            [{"meta_post_id":"18123456789012345","source":"cache_unknown",
              "published_at":post()["timestamp"]}])
        result=collect(db,now=NOW,load=lambda db,refresh:("secret-test","dohay_dilam"),read=reader)
        self.assertEqual(result["state"],"readback_unverified")
        self.assertEqual(result["verified_count"],0)

    def test_duplicated_feed_post_only_one_db_observation(self):
        arr=parse_posts({"data":[post(),post()]},now=NOW)
        self.assertEqual(len(arr),1)

if __name__=="__main__":
    unittest.main()
