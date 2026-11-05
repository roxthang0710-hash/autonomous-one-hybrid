import tempfile,unittest,json
from pathlib import Path
from PIL import Image
from scripts.enna_photo_memes import trusted,cc0,render,compose
class PhotoTests(unittest.TestCase):
 def test_sources_and_license(self):
  self.assertTrue(trusted("https://upload.wikimedia.org/wikipedia/commons/a.jpg"))
  self.assertFalse(trusted("https://upload.wikimedia.org.evil.test/wikipedia/commons/a.jpg"))
  self.assertTrue(cc0({"mime":"image/jpeg","extmetadata":{"LicenseShortName":{"value":"CC0 1.0"}}}))
  self.assertFalse(cc0({"mime":"image/jpeg","extmetadata":{"LicenseShortName":{"value":"CC BY-SA 4.0"}}}))
 def test_three_rendered_drafts(self):
  photo=Image.new("RGB",(1400,950),"#78918b")
  def fake(s):return photo,{"source":s[1],"license":"CC0 1.0"}
  with tempfile.TemporaryDirectory() as d:
   files=render(d,fetch=fake)
   self.assertEqual(len(files),3)
   for path in files:
    self.assertEqual(Image.open(path).size,(1080,1350))
    meta=json.loads(Path(path).with_suffix(".rights.json").read_text())
    self.assertEqual(meta["status"],"DRAFT_REQUIRES_HUMAN_REVIEW")
    self.assertFalse(meta["published"])
if __name__=="__main__":unittest.main()
