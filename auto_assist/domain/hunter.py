from bs4 import BeautifulSoup
import requests
import os

from auto_assist.lib import url_to_filename


class ChemistryHunterCmd:

    def __init__(self,
                 pandoc_cmd='pandoc',
                 pandoc_opt='-f html-native_divs-native_spans -t markdown',
                 browser_dir=None,
                 proxy=None):
        """
        Camnnd line interface to the Chemistry Hunter

        :param pandoc_cmd: str
            The command to run pandoc
        :param proxy: str
            The proxy to use for requests and playwright
        """
        self._pancdo_cmd = pandoc_cmd
        self._pandoc_opt = pandoc_opt
        self._proxy = proxy
        self._browser_dir = browser_dir

    def scrape_urls(self, urls_file: str, out_dir: str):
        os.makedirs(out_dir, exist_ok=True)
        with open(urls_file) as f:
            for url in f:
                url = url.strip()
                if not url:
                    continue
                filename = url_to_filename(url)
                out_file = os.path.join(out_dir, filename)
                if os.path.exists(out_file):
                    print('skip {} as file {} exist'.format(url, out_file))
                    continue
                print('scraping {}'.format(url))
                resp = self._requests_get(url)
                resp.raise_for_status()
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(resp.text)

    def convert_html_to_md(self, input_htmls, out_dir):
        ...

    def retrive_briefs(self, input_files, out_dir):
        ...

    def google_cv(self, input_files, out_dir):
        ...

    def retrive_former_team_in_cv(self, input_files, out_dir):
        ...

    def google_former_team(self, input_files, out_dir):
        ...

    def retrive_team_members(self, input_files, out_dir):
        ...

    def _requests_get(self, url):
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0 '
        if self._proxy:
            proxies = {
                'http': self._proxy,
                'https': self._proxy
            }
        else:
            proxies = None
        return requests.get(url, proxies=proxies, headers={'User-Agent': user_agent})

