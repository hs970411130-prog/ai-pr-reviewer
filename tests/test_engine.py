import unittest
from src.analyzer.engine import filter_code_files, chunk_files, find_skipped_files
from src.models import FileChange, ChangeType


def _fc(filename, diff_len=100):
    return FileChange(filename=filename, change_type=ChangeType.MODIFIED, diff="x" * diff_len)


class TestFilterCodeFiles(unittest.TestCase):
    def test_keeps_py(self):
        self.assertEqual(len(filter_code_files([_fc("a.py")])), 1)

    def test_filters_md(self):
        self.assertEqual(len(filter_code_files([_fc("README.md")])), 0)

    def test_filters_json(self):
        self.assertEqual(len(filter_code_files([_fc("pkg.json")])), 0)

    def test_mixed(self):
        changes = [_fc("a.py"), _fc("b.md"), _fc("c.js")]
        result = filter_code_files(changes)
        self.assertEqual(len(result), 2)


class TestChunkFiles(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(chunk_files([]), [])

    def test_single(self):
        batches = chunk_files([_fc("a.py")])
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), 1)

    def test_max_batch(self):
        changes = [_fc(f"f{i}.py") for i in range(7)]
        batches = chunk_files(changes)
        self.assertEqual(len(batches), 3)

    def test_skips_large(self):
        changes = [_fc("small.py", 100), _fc("big.py", 20000), _fc("s2.py", 50)]
        batches = chunk_files(changes)
        all_f = [c.filename for b in batches for c in b]
        self.assertNotIn("big.py", all_f)
        self.assertIn("small.py", all_f)


class TestSkipped(unittest.TestCase):
    def test_none(self):
        self.assertEqual(find_skipped_files([_fc("a.py", 100)]), [])

    def test_has_skipped(self):
        changes = [_fc("a.py", 100), _fc("big.py", 20000)]
        self.assertEqual(find_skipped_files(changes), ["big.py"])


if __name__ == "__main__":
    unittest.main()
