import unittest
from memory import recall, normalize, memory_context
from simulator import simulate
class MemoryTests(unittest.TestCase):
 def test_vietnamese_accents(self):
  self.assertEqual(normalize('Đánh GIÁ — ý tưởng!'),'danh gia y tuong')
 def test_same_problem_different_title(self):
  old={'title':'Bảng tổng hợp tuần','problem_hypothesis':'Nhân viên mất nhiều thời gian nhập báo cáo thủ công','target_customer':'Bộ phận tiếp thị khách sạn'}
  new={**old,'title':'Trợ lý số liệu tự động'}
  r=recall(new,[{'id':'prior','proposal':old,'approval_status':'rejected'}])
  self.assertTrue(r['duplicate']);self.assertEqual(r['prior_decision'],'rejected')
 def test_empty_not_duplicate(self):self.assertFalse(recall({},[{'proposal':{}}])['duplicate'])
 def test_different_customers_and_titles(self):
  self.assertFalse(recall({'title':'Lịch chăm sóc cây','target_customer':'người làm vườn','problem_hypothesis':'quên tưới cây'},[{'proposal':{'title':'Kế toán khách sạn','target_customer':'kế toán','problem_hypothesis':'nhập báo cáo'}}])['duplicate'])
 def test_bounded_context(self):self.assertEqual(len(memory_context([{'proposal':{}}]*100)),40)
 def test_extreme_simulation_rejected(self):
  with self.assertRaises(ValueError):simulate(price_vnd=1e308)
