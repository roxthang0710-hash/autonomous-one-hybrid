import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

from PIL import Image
from growth.visual_review_catalog import (verify_draft, storage_upload,
    catalog_row, publish_review_drafts)

class VisualCatalogTests(unittest.TestCase):
    def make_file(self, folder):
        file=Path(folder)/"2026-11-06-coffee.png"
        image=Image.effect_noise((1080,1350),32).convert("RGB")
        image.save(file,format="PNG")
        proof={
          "status":"DRAFT_REQUIRES_HUMAN_REVIEW","published":False,
          "license":"CC0 1.0","fictional_joke_not_factual_claim":True,
          "visual_source_page":"https://commons.wikimedia.org/wiki/File:Coffee_cup.jpg",
          "commons_filename":"File:Coffee cup.jpg","author":"Original Author",
          "image_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
          "source_photo_sha256":"a"*64,
          "headline":"MỚI CHÍN GIỜ SÁNG",
          "punchline":"Cốc cà phê chưa uống xong, cuộc họp đã bắt đầu.",
          "visual_hint":"một cốc cà phê trên bàn",
          "format":"minimal","copy_origin":"human_curated"
        }
        file.with_suffix(".rights.json").write_text(
            json.dumps(proof,ensure_ascii=False),encoding="utf-8")
        return file

    def test_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as f:
            file=self.make_file(f)
            self.assertEqual(verify_draft(file)[0]["license"],"CC0 1.0")
            file.write_bytes(file.read_bytes()+b"tampered")
            with self.assertRaisesRegex(ValueError,"image-hash-mismatch"):
                verify_draft(file)

    def test_only_needs_review_non_auto_publishable(self):
        with tempfile.TemporaryDirectory() as f:
            file=self.make_file(f)
            proof,digest,raw=verify_draft(file)
            row=catalog_row(proof,digest,"https://example.test/approved.png")
            self.assertEqual(row["media_type"],"licensed_photo")
            self.assertEqual(row["status"],"needs_review")
            self.assertEqual(row["rights_status"],"review_required")
            self.assertTrue(row["evidence"]["not_auto_publishable"])
            self.assertFalse(row["evidence"]["human_visual_approval"])

    def test_registration_must_readback_correct_status(self):
        with tempfile.TemporaryDirectory() as f:
            file=self.make_file(f)
            db=Mock()
            url="https://example.test/review.png"
            def fake_request(method,route,**kwargs):
                if method=="POST":
                    self.assertEqual(kwargs["payload"]["status"],"needs_review")
                    self.assertEqual(kwargs["payload"]["media_type"],"licensed_photo")
                    return [{"idea_key":"some"}]
                row=kwargs["params"]
                return [{"idea_key":row["idea_key"][3:],"status":"needs_review",
                    "media_type":"licensed_photo","rights_status":"review_required",
                    "source_url":url}]
            db.request.side_effect=fake_request
            output=publish_review_drafts(f,upload=lambda *args:url,db=db)
            self.assertEqual(len(output),1)
            self.assertEqual(db.request.call_count,2)

    def test_conflicting_registration_is_not_confirmed(self):
        with tempfile.TemporaryDirectory() as f:
            self.make_file(f)
            db=Mock()
            db.request.side_effect=[[{"ok":True}],[{"status":"ready","rights_status":"original"}]]
            with self.assertRaisesRegex(RuntimeError,"review-registration-not-confirmed"):
                publish_review_drafts(f,upload=lambda *args:"https://example.test/x.png",db=db)

    def test_409_only_succeeds_if_public_file_is_a_png(self):
        response=Mock(status_code=409)
        head=Mock(return_value=Mock(status_code=200,headers={"Content-Type":"image/png"}))
        post=Mock(return_value=response)
        with patch.dict(os.environ,{"SUPABASE_URL":"https://test.supabase.co","DB_SERVICE_KEY":"fake-secret"}):
            self.assertIn("/visual-review/",storage_upload("visual-review/a.png",b"png",post=post,head=head))
            head.return_value.status_code=404
            with self.assertRaisesRegex(RuntimeError,"storage-upload-not-confirmed"):
                storage_upload("visual-review/a.png",b"png",post=post,head=head)

if __name__=="__main__":
    unittest.main()
