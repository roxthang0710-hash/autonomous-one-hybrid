import unittest
from evaluator import evaluate_proposal, VERSION


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.proposal = {
            "title": "Tạo công cụ báo cáo cho doanh nghiệp nhỏ",
            "success_metric": "Có ít nhất 10 người đăng ký trải nghiệm trong 7 ngày",
            "zero_cost_experiment": (
                "Phác thảo công cụ bằng bộ dữ liệu giả, tạo một trang mẫu giới thiệu "
                "chức năng và kiểm tra độ chính xác với bộ bài thử có sẵn."
            ),
            "estimated_cost_vnd": 0,
            "risks": ["Dữ liệu thử không đại diện", "Ít người dùng quan tâm"],
        }

    def test_score_is_bounded_and_unvalidated(self):
        x = evaluate_proposal(self.proposal, [{}, {}, {}])
        self.assertTrue(0 <= x["score"] <= 100)
        self.assertEqual(x["evidence_status"], "unvalidated")
        self.assertEqual(x["evaluator_version"], VERSION)

    def test_duplicate_penalty(self):
        original = evaluate_proposal(self.proposal, [])
        duplicate = evaluate_proposal(self.proposal, [], [self.proposal["title"]])
        self.assertEqual(original["score"] - duplicate["score"], 35)
        self.assertTrue(any("tương tự" in s for s in duplicate["findings"]))

    def test_paid_plan_not_considered_zero_cost(self):
        proposal = dict(self.proposal, estimated_cost_vnd=100_000)
        result = evaluate_proposal(proposal, [])
        self.assertEqual(result["rubric"]["zero_cost"]["points"], 0)

    def test_empty_proposal_scores_zero(self):
        x = evaluate_proposal({}, [])
        self.assertEqual(x["score"], 0)
        self.assertEqual(x["verdict"], "hold")


if __name__ == "__main__":
    unittest.main()
