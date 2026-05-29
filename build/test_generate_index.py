import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from generate_index import parse_head, git_last_modified


class ParseHeadTests(unittest.TestCase):
    def test_reads_title_and_description(self):
        html_text = (
            "<html><head>"
            "<title>My Spec</title>"
            '<meta name="description" content="A spec doc">'
            "</head><body>ignored</body></html>"
        )
        title, description = parse_head(html_text)
        self.assertEqual(title, "My Spec")
        self.assertEqual(description, "A spec doc")

    def test_missing_title_and_description_return_none(self):
        title, description = parse_head("<html><head></head><body>x</body></html>")
        self.assertIsNone(title)
        self.assertIsNone(description)

    def test_title_whitespace_is_stripped(self):
        title, _ = parse_head("<head><title>  Spaced  </title></head>")
        self.assertEqual(title, "Spaced")


class GitLastModifiedTests(unittest.TestCase):
    def test_returns_commit_date_for_tracked_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            env = {
                **os.environ,
                "GIT_AUTHOR_DATE": "2026-05-20T00:00:00",
                "GIT_COMMITTER_DATE": "2026-05-20T00:00:00",
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            }
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            f = repo / "a.html"
            f.write_text("<title>x</title>")
            subprocess.run(["git", "add", "a.html"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=repo, env=env, check=True)
            self.assertEqual(git_last_modified(f), "2026-05-20")

    def test_returns_none_for_untracked_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            f = repo / "b.html"
            f.write_text("<title>x</title>")
            self.assertIsNone(git_last_modified(f))


if __name__ == "__main__":
    unittest.main()
