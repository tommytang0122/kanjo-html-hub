"""Generate the kanjo-html-hub index page from files under projects/."""

import html
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path


class _StopParsing(Exception):
    """Raised to stop parsing once </head> is reached."""


class _HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.description = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            attrs_dict = dict(attrs)
            if (attrs_dict.get("name") or "").lower() == "description":
                content = (attrs_dict.get("content") or "").strip()
                self.description = content or None

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            raise _StopParsing

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data


def parse_head(html_text):
    """Return (title, description); each is None when absent."""
    parser = _HeadParser()
    try:
        parser.feed(html_text)
    except _StopParsing:
        pass
    title = parser.title.strip() if parser.title else None
    return (title or None), parser.description


def git_last_modified(path):
    """Return the last commit date (YYYY-MM-DD) for path, or None."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path.name)],
            cwd=str(path.parent),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    value = result.stdout.strip()
    return value or None


def make_entry(html_path, projects_dir):
    """Build one index entry dict from an HTML file path."""
    text = html_path.read_text(encoding="utf-8", errors="replace")
    title, description = parse_head(text)
    if not title:
        title = html_path.stem
    href = html_path.relative_to(projects_dir.parent).as_posix()
    project = html_path.relative_to(projects_dir).parts[0]
    return {
        "title": title,
        "description": description,
        "project": project,
        "href": href,
        "updated": git_last_modified(html_path),
    }


def collect_entries(projects_dir):
    """Return an ordered dict {project: [entry, ...]} for all *.html under projects_dir."""
    groups = {}
    if projects_dir.is_dir():
        for path in sorted(projects_dir.rglob("*.html")):
            entry = make_entry(path, projects_dir)
            groups.setdefault(entry["project"], []).append(entry)
    for items in groups.values():
        items.sort(key=lambda e: (e["updated"] or ""), reverse=True)
    return dict(sorted(groups.items()))


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kanjo-html-hub</title>
<link rel="stylesheet" href="assets/index.css">
</head>
<body>
<main>
<h1>kanjo-html-hub</h1>
{body}
</main>
</body>
</html>
"""


def render_index(groups):
    """Render the full index page HTML from grouped entries."""
    esc = html.escape
    if not groups:
        body = '<p class="empty">尚無內容</p>'
    else:
        sections = []
        for project, items in groups.items():
            rows = []
            for entry in items:
                meta = []
                if entry["description"]:
                    meta.append(f'<span class="desc">{esc(entry["description"])}</span>')
                if entry["updated"]:
                    meta.append(f'<span class="date">{esc(entry["updated"])}</span>')
                meta_html = "".join(meta)
                rows.append(
                    f'<li><a href="{esc(entry["href"])}">{esc(entry["title"])}</a>'
                    f"{meta_html}</li>"
                )
            sections.append(
                f'<section><h2>{esc(project)}</h2>\n<ul>\n'
                + "\n".join(rows)
                + "\n</ul></section>"
            )
        body = "\n".join(sections)
    return _PAGE_TEMPLATE.format(body=body)


def build(root, out_dir):
    """Generate out_dir: a copy of projects/ + assets/ plus a fresh index.html."""
    projects_dir = root / "projects"
    groups = collect_entries(projects_dir)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    if projects_dir.is_dir():
        shutil.copytree(projects_dir, out_dir / "projects")
    assets_dir = root / "assets"
    if assets_dir.is_dir():
        shutil.copytree(assets_dir, out_dir / "assets")

    (out_dir / "index.html").write_text(render_index(groups), encoding="utf-8")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    build(repo_root, repo_root / "_site")
    print("Built _site/")
