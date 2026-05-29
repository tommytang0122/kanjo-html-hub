import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from generate_index import parse_head, git_last_modified, collect_entries, render_index, build


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


class CollectEntriesTests(unittest.TestCase):
    def _write(self, base, rel, body):
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_groups_by_top_level_folder_and_falls_back_to_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            self._write(projects, "alpha/spec.html", "<head><title>Spec A</title></head>")
            self._write(projects, "alpha/nested/deep.html", "<head></head>")
            self._write(projects, "beta/report.html", "<head><title>Report B</title></head>")

            groups = collect_entries(projects)

            self.assertEqual(list(groups.keys()), ["alpha", "beta"])
            titles = {e["title"] for e in groups["alpha"]}
            self.assertEqual(titles, {"Spec A", "deep"})  # deep.html has no title
            href = groups["beta"][0]["href"]
            self.assertEqual(href, "projects/beta/report.html")

    def test_missing_projects_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(collect_entries(Path(tmp) / "projects"), {})

    def test_href_is_url_encoded_for_reserved_chars(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / "projects"
            self._write(projects, "demo/a b & c.html", "<head><title>X</title></head>")
            groups = collect_entries(projects)
            href = groups["demo"][0]["href"]
            self.assertEqual(href, "projects/demo/a%20b%20%26%20c.html")
            self.assertNotIn(" ", href)


class RenderIndexTests(unittest.TestCase):
    def test_renders_project_sections_and_links(self):
        groups = {
            "alpha": [
                {"title": "Spec A", "description": "desc", "project": "alpha",
                 "href": "projects/alpha/spec.html", "updated": "2026-05-20"},
            ]
        }
        out = render_index(groups)
        self.assertIn("<h2>alpha</h2>", out)
        self.assertIn('href="projects/alpha/spec.html"', out)
        self.assertIn("Spec A", out)
        self.assertIn("2026-05-20", out)
        self.assertIn("desc", out)

    def test_escapes_html_in_titles(self):
        groups = {
            "alpha": [
                {"title": "<script>", "description": None, "project": "alpha",
                 "href": "projects/alpha/x.html", "updated": None},
            ]
        }
        out = render_index(groups)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_empty_groups_show_placeholder(self):
        out = render_index({})
        self.assertIn("尚無內容", out)


class BuildTests(unittest.TestCase):
    def test_build_copies_projects_and_assets_and_writes_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "projects" / "alpha").mkdir(parents=True)
            (root / "projects" / "alpha" / "spec.html").write_text(
                "<head><title>Spec A</title></head>", encoding="utf-8"
            )
            (root / "assets").mkdir()
            (root / "assets" / "index.css").write_text("body{}", encoding="utf-8")
            out = root / "_site"

            build(root, out)

            self.assertTrue((out / "index.html").exists())
            self.assertTrue((out / "projects" / "alpha" / "spec.html").exists())
            self.assertTrue((out / "assets" / "index.css").exists())
            self.assertIn("Spec A", (out / "index.html").read_text(encoding="utf-8"))

    def test_build_overwrites_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "projects").mkdir()
            out = root / "_site"
            out.mkdir()
            (out / "stale.txt").write_text("old", encoding="utf-8")

            build(root, out)

            self.assertFalse((out / "stale.txt").exists())
            self.assertTrue((out / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
