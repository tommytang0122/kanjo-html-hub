"""Generate the kanjo-html-hub index page from files under projects/."""

from html.parser import HTMLParser


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
