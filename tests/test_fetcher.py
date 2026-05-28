import unittest
from unittest.mock import patch
from src.fetcher.github import parse_pr_url, GitHubFetcher


class TestParsePrUrl(unittest.TestCase):
    def test_standard_url(self):
        owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/42")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")
        self.assertEqual(num, 42)

    def test_url_with_extra_segments(self):
        owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/42/files")
        self.assertEqual(owner, "owner")
        self.assertEqual(num, 42)

    def test_invalid_url_raises(self):
        with self.assertRaises(ValueError):
            parse_pr_url("https://github.com/owner/repo")


class TestGitHubFetcher(unittest.TestCase):
    def test_no_token_still_works(self):
        import os
        old = os.environ.pop("GITHUB_TOKEN", None)
        try:
            fetcher = GitHubFetcher(token="")
            self.assertIsNotNone(fetcher)
        finally:
            if old:
                os.environ["GITHUB_TOKEN"] = old


if __name__ == "__main__":
    unittest.main()
