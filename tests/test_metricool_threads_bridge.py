"""A2.2 evidence bridge: no mutable remote writes, exact source provenance."""
import json
import unittest
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path

from growth.metricool_threads_bridge import (
    BRAND, COPY, SNAPSHOT, canonical, date, make_seed,
    match_pairs, seed, reconcile,
)

NOW=datetime(2026,11,6,15,0,tzinfo=timezone.utc)
POSTID="18139136707630681"
UUID="8595030504777599850"
URL="https://www.threads.com/@dohay_dilam/post/DfYiccaignm"


def link(uuid=UUID,status="PUBLISHED",sha=None,posted_url=URL,at=NOW-timedelta(hours=12)):
    return {"brand_key":BRAND,"metricool_uuid":uuid,
      "metricool_post_id":"418135116",
      "scheduled_at":at.isoformat(),"provider_status_last_seen":status,
      "provider_permalink":posted_url,"expected_text_sha256":sha,
      "provider_observed_at":NOW.isoformat(),
      "provider_source":"metricool_owner_connector_snapshot",
      "meta_post_id":None}


def official(metaid=POSTID,link_url=URL,sha=None,at=NOW-timedelta(hours=12)):
    return {"meta_post_id":metaid,"published_at":at.isoformat(),
      "permalink":link_url,"text_sha256":sha,"source":"meta_official"}


class MemoryDb:
    def __init__(self,links=None,obs=None,legacy=None):
        self.links={x["metricool_uuid"]:deepcopy(x) for x in (links or [])}
        self.official=deepcopy(obs or [])
        self.legacy=deepcopy(legacy or {})
        self.calls=[]
        self.bad_readback=False

    def request(self,method,path,params=None,payload=None,prefer=None):
        self.calls.append((method,path,deepcopy(params),deepcopy(payload)))
        if method=="POST" and path=="/enna_metricool_threads_links":
            out=[]
            for obj in payload:
                key=obj["metricool_uuid"]
                if key not in self.links:
                    self.links[key]=deepcopy(obj)
                    out.append(obj)
            return out
        if method=="GET" and path=="/enna_metricool_threads_links":
            if self.bad_readback:return None
            key=(params or {}).get("metricool_uuid")
            if key:
                a=self.links.get(key.removeprefix("eq."))
                return [deepcopy(a)] if a else []
            return deepcopy(list(self.links.values()))
        if method=="PATCH" and path=="/enna_metricool_threads_links":
            k=params["metricool_uuid"].removeprefix("eq.")
            row=self.links.get(k)
            if not row or row.get("meta_post_id"):
                return []
            row.update(deepcopy(payload))
            return [deepcopy(row)]
        if method=="GET" and path=="/enna_official_threads_observations":
            return deepcopy(self.official)
        if method=="GET" and path=="/threads_metricool_schedule":
            q=params["metricool_uuid"].removeprefix("eq.")
            return [{"post_id":"internal-uuid","metricool_uuid":q,"provider":"threads"}] if q in self.legacy else []
        if path=="/threads_posts":
            if method=="GET":
                return [deepcopy(self.legacy["internal-uuid"])] if "internal-uuid" in self.legacy else []
            if method=="PATCH":
                row=self.legacy.get("internal-uuid")
                if not row or row["status"]!="scheduled_external":
                    return []
                row.update(deepcopy(payload))
                return [deepcopy(row)]
        raise AssertionError("Unexpected request "+str((method,path)))


class BridgeTests(unittest.TestCase):
    def test_live_snapshot_has_all_expected_provider_records(self):
        snap=json.loads(Path(SNAPSHOT).read_text(encoding="utf-8"))
        copy=json.loads(Path(COPY).read_text(encoding="utf-8"))
        records=make_seed(snap,copy)
        self.assertEqual(len(records),38)
        self.assertEqual(sum(x["provider_status_last_seen"]=="PUBLISHED" for x in records),17)
        self.assertEqual(sum(x["provider_status_last_seen"]=="PENDING" for x in records),21)
        self.assertTrue(all(x["expected_text_sha256"] for x in records
                            if x["provider_status_last_seen"]=="PENDING"))
        self.assertFalse(any("text_content" in x or "access_token" in x for x in records))

    def test_no_weak_or_improper_provider_urls(self):
        self.assertEqual(canonical(URL),"DfYiccaignm")
        for bad in (None,"https://evil.com/@dohay_dilam/post/DfYiccaignm",
                    "http://www.threads.com/@dohay_dilam/post/DfYiccaignm",
                    "https://www.threads.com/@someone_else/post/DfYiccaignm",
                    "https://www.threads.com/@dohay_dilam/post/short",
                    "https://www.threads.com@evil.com/@dohay_dilam/post/DfYiccaignm"):
            self.assertIsNone(canonical(bad))

    def test_exact_permalink_overrides_old_caption_drift(self):
        pairs=match_pairs([link()],[official()],now=NOW)
        self.assertEqual(len(pairs),1)
        self.assertEqual(pairs[0]["meta_post_id"],POSTID)
        self.assertEqual(pairs[0]["match_basis"],"exact_verified_permalink")

    def test_hash_time_will_work_for_future_unchanged_pending_caption(self):
        import hashlib
        sha=hashlib.sha256("Câu chuyện đã duyệt".encode()).hexdigest()
        due=NOW-timedelta(minutes=2)
        src=link(status="PENDING",posted_url=None,sha=sha,at=due)
        meta=official(sha=sha,at=due+timedelta(minutes=1))
        got=match_pairs([src],[meta],now=NOW)
        self.assertEqual(len(got),1)
        self.assertEqual(got[0]["match_basis"],"unique_caption_hash_and_time")

    def test_edited_caption_does_not_get_guessed_from_time_alone(self):
        due=NOW-timedelta(minutes=3)
        src=link(status="PENDING",posted_url=None,sha="a"*64,at=due)
        meta=official(sha="b"*64,at=due)
        self.assertEqual(match_pairs([src],[meta],now=NOW),[])

    def test_ambiguous_two_scheduled_to_one_meta_id_never_match(self):
        due=NOW-timedelta(minutes=3)
        src=[link(uuid="123456789",status="PENDING",posted_url=None,sha="a"*64,at=due),
             link(uuid="234567890",status="PENDING",posted_url=None,sha="a"*64,at=due)]
        self.assertEqual(match_pairs(src,[official(sha="a"*64,at=due)],now=NOW),[])

    def test_same_permalink_to_two_official_ids_is_ambiguous(self):
        self.assertEqual(match_pairs([link()],
            [official(),official(metaid="18123456780000001")],now=NOW),[])

    def test_bootstrap_is_idempotent_and_readback_verified(self):
        db=MemoryDb()
        first=seed(db)
        second=seed(db)
        self.assertEqual(first["state"],"bootstrap_verified")
        self.assertEqual(first["inserted_now"],38)
        self.assertEqual(second["inserted_now"],0)
        self.assertEqual(len(db.links),38)
        self.assertFalse(any(c[1].startswith("/threads") for c in db.calls))

    def test_exact_verified_link_repairs_stale_internal_ledger_once(self):
        db=MemoryDb(links=[link()],obs=[official()],legacy={
            UUID:{"dummy":True},
            "internal-uuid":{"id":"internal-uuid","status":"scheduled_external",
                "platform_post_id":None}})
        first=reconcile(db,now=NOW)
        self.assertEqual(first["linked_verified"],1)
        self.assertEqual(first["legacy_ledger_repaired"],1)
        self.assertEqual(db.legacy["internal-uuid"]["platform_post_id"],POSTID)
        second=reconcile(db,now=NOW+timedelta(minutes=2))
        self.assertEqual(second["linked_verified"],0)
        self.assertEqual(second["legacy_ledger_repaired"],0)
        self.assertFalse(any(c[0]=="POST" and c[1]!="/enna_metricool_threads_links" for c in db.calls))
        self.assertFalse(any("threads_publish" in c[1] for c in db.calls))

    def test_hash_match_only_updates_bridge_not_legacy_publication(self):
        due=NOW-timedelta(minutes=2)
        db=MemoryDb(links=[link(status="PENDING",posted_url=None,sha="e"*64,at=due)],
                    obs=[official(sha="e"*64,at=due+timedelta(minutes=1))],
                    legacy={UUID:{"dummy":True},
                            "internal-uuid":{"id":"internal-uuid","status":"scheduled_external","platform_post_id":None}})
        out=reconcile(db,now=NOW)
        self.assertEqual(out["hash_time_matches"],1)
        self.assertEqual(out["legacy_ledger_repaired"],0)
        self.assertEqual(db.legacy["internal-uuid"]["status"],"scheduled_external")

    def test_missing_official_source_does_not_claim_success(self):
        class BrokenDb(MemoryDb):
            def request(self,method,path,params=None,payload=None,prefer=None):
                if path=="/enna_official_threads_observations":
                    return None
                return super().request(method,path,params=params,payload=payload,prefer=prefer)
        with self.assertRaises(RuntimeError):
            reconcile(BrokenDb(links=[link()]),now=NOW)

    def test_incomplete_readback_raises_not_success(self):
        db=MemoryDb(links=[link()],obs=[official()])
        db.bad_readback=True
        with self.assertRaises(RuntimeError):
            reconcile(db,now=NOW)


if __name__=="__main__":
    unittest.main()
