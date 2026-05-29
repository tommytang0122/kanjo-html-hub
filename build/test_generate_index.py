import unittest

from generate_index import parse_head


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


if __name__ == "__main__":
    unittest.main()
