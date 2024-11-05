from bs4 import BeautifulSoup
import subprocess as sp
import requests
import os

from auto_assist.lib import url_to_filename, expand_globs



class ChemistryHunterCmd:

    def __init__(self,
                 pandoc_cmd='pandoc',
                 pandoc_opt='-f html -t markdown_strict-raw_html',
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
                    print(f'skip {url} as {out_file} already exists')
                    continue
                print(f'scraping {url}')
                resp = self._requests_get(url)
                resp.raise_for_status()
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(resp.text)


    def convert_html_to_md(self, *html_files: str, out_dir: str):
        """
        Convert html files to markdown files with pandoc

        :param html_files: list of str
            The html files to convert
        :param out_dir: str
        """
        in_files = expand_globs(html_files)
        os.makedirs(out_dir, exist_ok=True)
        for in_file in in_files:
            filename = os.path.basename(in_file)
            out_file = os.path.join(out_dir, filename + '.md')
            print(f'converting {in_file} to {out_file}')
            sp.check_call(f'{self._pancdo_cmd} {self._pandoc_opt} {in_file} -o {out_file}', shell=True)

    def clean_html(self, *html_files: str, out_dir = None):
        """
        Clean html files

        :param html_files: list of str
            The html files to clean
        :param out_dir: st
            The output directory, if None, will overwrite the input files
        """
        if out_dir is not None:
            os.makedirs(out_dir, exist_ok=True)
        in_files = expand_globs(html_files)
        for in_file in in_files:
            filename = os.path.basename(in_file)
            out_file = os.path.join(out_dir, filename) if out_dir else in_file
            print(f'cleaning {in_file} to {out_file}')
            with open(in_file, encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                # remove base64 images
                for img in soup.find_all('img'):
                    if img.get('src', '').startswith('data:image'):
                        img.decompose()
                # remove svg images
                for svg in soup.find_all('svg'):
                    svg.decompose()
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

    def retrive_briefs(self, in_files, out_dir):
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

