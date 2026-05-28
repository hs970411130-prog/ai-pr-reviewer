import unittest
from src.reporter.confidence import deduplicate_risks, deduplicate_suggestions, confidence_label
from src.models import RiskFinding, SuggestionFinding


class TestDedup(unittest.TestCase):
    def test_risk_dup(self):
        risks = [
            RiskFinding(file="a.py", line=1, risk_type="SQL", description="first"),
            RiskFinding(file="a.py", line=1, risk_type="SQL", description="second"),
        ]
        result = deduplicate_risks(risks)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].description, "first")

    def test_suggestion_dup(self):
        s = [
            SuggestionFinding(file="a.py", line=1, category="s", description="a"),
            SuggestionFinding(file="a.py", line=1, category="s", description="b"),
        ]
        self.assertEqual(len(deduplicate_suggestions(s)), 1)


class TestLabel(unittest.TestCase):
    def test_all_levels(self):
        for i in range(1, 6):
            self.assertIsInstance(confidence_label(i), str)


if __name__ == "__main__":
    unittest.main()
