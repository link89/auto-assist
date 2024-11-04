from unittest import TestCase

from auto_assist.lib import url_to_filename


class TestLib(TestCase):

    def test_url_to_filename(self):
        url = 'https://www.google.com/search?q=python'
        filename = url_to_filename(url)
        self.assertEqual(filename, 'www.google.com_search.html')