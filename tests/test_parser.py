import unittest
from src.parser.diff_parser import (
    extract_added_lines, extract_removed_lines,
    is_empty_diff, count_diff_hunks,
)
from src.models import FileChange, ChangeType


class TestExtractLines(unittest.TestCase):
    def test_added_lines(self):
        self.assertEqual(extract_added_lines(""), [])
        diff = "@@ -1,0 +1,1 @@\n+new line"
        self.assertEqual(extract_added_lines(diff), ["new line"])

    def test_skips_diff_headers(self):
        self.assertEqual(extract_added_lines("+++ b/file.py"), [])

    def test_removed_lines(self):
        diff = "@@ -1,2 +1,1 @@\n-old line\n context"
        self.assertEqual(extract_removed_lines(diff), ["old line"])

    def test_removed_skips_header(self):
        self.assertEqual(extract_removed_lines("--- a/file.py"), [])


class TestEmptyDiff(unittest.TestCase):
    def test_empty(self):
        fc = FileChange(filename="x.py", change_type=ChangeType.MODIFIED, diff="")
        self.assertTrue(is_empty_diff(fc))

    def test_not_empty(self):
        fc = FileChange(filename="x.py", change_type=ChangeType.MODIFIED, diff="@@ -1 +1 @@")
        self.assertFalse(is_empty_diff(fc))


class TestCountHunks(unittest.TestCase):
    def test_zero(self):
        fc = FileChange(filename="x.py", change_type=ChangeType.MODIFIED, diff="")
        self.assertEqual(count_diff_hunks(fc), 0)

    def test_two(self):
        diff = "@@ -1,3 +1,3 @@\n@@ -10,3 +10,3 @@"
        fc = FileChange(filename="x.py", change_type=ChangeType.MODIFIED, diff=diff)
        self.assertEqual(count_diff_hunks(fc), 2)


if __name__ == "__main__":
    unittest.main()
