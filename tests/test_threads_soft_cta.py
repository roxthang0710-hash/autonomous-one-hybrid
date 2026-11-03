"""Regression tests for sparse, human-sounding follow invitations."""
import unittest
from threads.content import should_offer_cta
from threads.planner import check_post

class SoftCtaTests(unittest.TestCase):
    def test_recent_follow_invitation_prevents_repetitive_cta(self):
        recent=[
          "Bàn gọn 10/10, tìm bút 0/10",
          "Hợp gu thì follow @dohay_dilam để cùng cười nhé.",
          "Chuyện văn phòng",
          "Mẹo nhỏ đi làm"
        ]
        self.assertFalse(should_offer_cta(recent))
    def test_no_recent_invitation_allows_optional_cta(self):
        self.assertTrue(should_offer_cta([
          "Đi làm rồi mới biết có 3 bản final.",
          "Một mẹo nhỏ sắp xếp đồ.",
          "Thứ Hai đến quá nhanh.",
          "Máy tính không tự sửa được."
        ]))
    def test_cta_must_not_break_existing_anti_spam_gate(self):
        caption=("Bàn làm việc gọn quá, đến lúc tìm bút cả phòng phải họp. "
                 "Hợp gu thì theo dõi @dohay_dilam để cùng cười nha. 😌")
        self.assertEqual(check_post(caption),[])

if __name__=="__main__":
    unittest.main()
