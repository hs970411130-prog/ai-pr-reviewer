import unittest
from unittest.mock import patch
from src.analyzer.summary import summarize, _build_file_list
from src.models import PRMetadata, FileChange, ChangeType


class TestBuildFileList(unittest.TestCase):
    def test_format(self):
        changes = [
            FileChange(filename="a.py", change_type=ChangeType.MODIFIED, diff="", additions=3, deletions=1),
            FileChange(filename="b.md", change_type=ChangeType.ADDED, diff="", additions=10, deletions=0),
        ]
        result = _build_file_list(changes)
        self.assertIn("[M] a.py", result)
        self.assertIn("(+3/-1)", result)
        self.assertIn("[+] b.md", result)


class TestSummarize(unittest.TestCase):
    def test_mocked_llm(self):
        meta = PRMetadata(owner="o", repo="r", pr_number=1, title="Add feature")
        changes = [FileChange(filename="a.py", change_type=ChangeType.MODIFIED, diff="@@ -1 +1 @@")]
        with patch("src.analyzer.summary.chat", return_value="test summary."):
            result = summarize(meta, changes)
            self.assertEqual(result, "test summary.")


if __name__ == "__main__":
    unittest.main()
