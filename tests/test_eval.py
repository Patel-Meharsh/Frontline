import unittest

import eval as evaluator


class EvaluationRubricTests(unittest.TestCase):
    def test_keyword_coverage_is_case_insensitive(self):
        score, missing = evaluator.keyword_coverage(
            "Please VERIFY the duplicate charge and review refund eligibility.",
            ["verify", "refund"],
        )
        self.assertEqual(score, 2)
        self.assertEqual(missing, [])

    def test_keyword_coverage_reports_missing_terms(self):
        score, missing = evaluator.keyword_coverage(
            "Ask the customer to resend the message.",
            ["resend", "readable"],
        )
        self.assertEqual(score, 1)
        self.assertEqual(missing, ["readable"])

    def test_no_rubric_returns_not_applicable(self):
        score, missing = evaluator.keyword_coverage("some text", [])
        self.assertIsNone(score)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
