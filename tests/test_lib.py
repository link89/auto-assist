from unittest import TestCase

from auto_assist.lib import url_to_key, get_md_code_block

md_text = """
```json
{"key": "value"}
```"""


class TestLib(TestCase):

    def test_url_to_filename(self):
        url = 'https://www.google.com/search?q=python'
        filename = url_to_key(url)
        self.assertEqual(filename, 'www.google.com_search.html')

    def test_get_md_code_block(self):
        data = next(get_md_code_block(md_text, '```json')).strip()
        self.assertEqual(data, '{"key": "value"}')