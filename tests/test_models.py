import unittest
from src.models import (
    PRMetadata, FileChange, ChangeType, RiskFinding,
    SuggestionFinding, ContextInfo, AnalysisReport,
)


class TestModels(unittest.TestCase):
    def test_pr_metadata_defaults(self):
        m = PRMetadata(owner="o", repo="r", pr_number=1, title="t")
        self.assertEqual(m.body, "")
        self.assertEqual(m.author, "")

    def test_filechange_defaults(self):
        fc = FileChange(filename="f.py", change_type=ChangeType.ADDED, diff="")
        self.assertEqual(fc.additions, 0)

    def test_risk_default_confidence(self):
        rf = RiskFinding(file="f", line=1, risk_type="t", description="d")
        self.assertEqual(rf.confidence, 3)

    def test_context_defaults(self):
        ctx = ContextInfo()
        self.assertEqual(ctx.related_issues, [])
        self.assertEqual(ctx.analysis_text, "")

    def test_report_defaults(self):
        meta = PRMetadata(owner="o", repo="r", pr_number=1, title="t")
        r = AnalysisReport(pr_metadata=meta)
        self.assertEqual(r.summary, "")
        self.assertEqual(r.risks, [])


if __name__ == "__main__":
    unittest.main()
