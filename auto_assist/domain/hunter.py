from bs4 import BeautifulSoup
from urllib.parse import urlparse

import requests

class ChemistryHunterCmd:

    def __init__(self, pandoc_cmd='pandoc', proxy=None):
        """
        Camnnd line interface to the Chemistry Hunter

        :param pandoc_cmd: str
            The command to run pandoc
        :param proxy: str
            The proxy to use for the requests
        """
        self._pancdo_cmd = pandoc_cmd
        self._proxy = proxy

    def _url_to_filename(self, url: str):
        """
        Convert url to a valid filename

        :param url: str
            The url to convert
        """

        parsed = urlparse(url)
        filename =  parsed.netloc + parsed.path.replace('/', '_')



    def scrape_faculty_pages(self, input_txt, out_dir):
        ...

    def convert_html_to_md(self, input_htmls, out_dir):
        ...

    def find_assistant_profs(self, input_mds, out_dir):
        ...

    def scrape_cv_with_google(self, input_files, out_dir):
        ...

