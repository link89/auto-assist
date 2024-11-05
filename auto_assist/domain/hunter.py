from typing import List
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import subprocess as sp
import requests
import asyncio
import os

from auto_assist.lib import url_to_filename, expand_globs
from auto_assist.browser import launch_browser



class ChemistryHunterCmd:

    def __init__(self,
                 pandoc_cmd='pandoc',
                 pandoc_opt='-f html -t gfm-raw_html',
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
        """
        Scrape urls to html files

        :param urls_file: str
            The file containing urls to scrape, one url per line
        :param out_dir: str
            The output directory
        """
        os.makedirs(out_dir, exist_ok=True)
        urls = list(_get_urls(urls_file))
        asyncio.run(self._async_scrape_urls(urls, out_dir))

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
        Clean html files to reduce size

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

    def retrive_faculty_members(self, urls_file, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        urls = list(_get_urls(urls_file))

        for url in urls:
            filename = url_to_filename(url)
            md_file = os.path.join(out_dir, filename + '.md')


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

    async def _async_scrape_urls(self, urls: List[str], out_dir: str):
        async with async_playwright() as pw:
            assert isinstance(self._browser_dir, str)
            browser = await launch_browser(self._browser_dir)(pw)
            page = browser.pages[0]
            # abort images, fonts, css and other media files
            await page.route('**/*.{png,jpg,jpeg,webp,css,woff,woff2,ttf,svg}', lambda route: route.abort())
            for url in urls:
                filename = url_to_filename(url)
                out_file = os.path.join(out_dir, filename)
                if os.path.exists(out_file):
                    print(f'skip {url} as {out_file} already exists')
                    continue
                print(f'scraping {url}')
                await page.goto(url)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(1)
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(await page.content())

def _get_urls(file):
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


retrive_faculty_member_prompt = """
Your job is to retrive information of faculty members from a markdown file.
The markdown file will contain multiple faculty members.

A faculty member object can be defined as the following TypeScript interface:

```typescript
interface FaucultyMember {
    name: string;
    title?: string;  // the title of the faculty member, e.g. Professor, Associate Professor, Prof, Enginner, etc.
    email?: string;
    institution?: string;  // the institution the faculty member belongs to
    department?: string;  // the department the faculty member belongs to
    introduction?: string;  // the introduction of the faculty member
    profile_url?: string; // the url to the detailed profile of the faculty member
    urls?: string[];  // other urls related to the faculty member
}
```

You must serialize every racultyMember object you find in the markdown file to a single line of json object, aka jsonl format,
and put them in a json block, for example:
```json
{"name": "Alice", "title": "Associate Professor", "profile_url": "https://example.org/alice", "email": "alice@example.org", "institution": "Example University", "department": "Computer Science"}
{"name": "Bob", "title": "Professor", "profile_url": "https://example.org/bob"}
```
""".strip()
