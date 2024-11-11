from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel
from typing import List

import pandas as pd
import subprocess as sp
import requests
import asyncio
import json
import os

from auto_assist.lib import (
    url_to_filename, expand_globs, get_logger,
    get_md_code_block, jsonl_load, jsonl_dump, dict_ignore_none)
from auto_assist.browser import launch_browser
from auto_assist import config

from . import prompt

logger = get_logger(__name__)

class HunterCmd:

    def __init__(self,
                 pandoc_cmd='pandoc',
                 pandoc_opt='-f html -t gfm-raw_html',
                 openai_log='./openai-log.jsonl',
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
        self._openai_log = openai_log

    def scrape_urls(self, excel_file: str, out_dir: str, col_name='FacultyPage'):
        """
        Scrape urls to html files

        :param excel_file: str
            The excel file that contains urls
        :param out_dir: str
            The output directory
        :param col_name: str
            The column name that contains urls
        """
        os.makedirs(out_dir, exist_ok=True)
        with open(excel_file, 'rb') as f:
            df = pd.read_excel(f)
        urls = list(df[col_name])
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
            logger.info(f'converting {in_file} to {out_file}')
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
            logger.info(f'cleaning {in_file} to {out_file}')
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

    def retrive_faculty_members(self, *md_files, out_dir):
        """
        Retrive faculty members from markdown files
        :param md_files: list of str
            The markdown files to retrive faculty members
        :param out_dir: str
            The output directory
        """
        os.makedirs(out_dir, exist_ok=True)
        openai_client = self._get_open_ai_client()
        for md_file in expand_globs(md_files):
            data_file = os.path.join(out_dir, os.path.basename(md_file) + '.jsonl')
            if os.path.exists(data_file):
                logger.info(f'{data_file} already exists, skip')
                continue
            with open(md_file, encoding='utf-8') as f:
                md_text = f.read()
            try:
                res = self._get_open_ai_response(openai_client,
                                                 prompt=prompt.RETRIVE_FACULTY_MEBERS,
                                                 text=md_text)
                answer = res.choices[0].message.content
                data = next(get_md_code_block(answer, '```json')).strip()
                with open(data_file, 'w', encoding='utf-8') as f:
                    f.write(data)
            except Exception as e:
                logger.exception(f'fail to retrive faculty members from {md_file}')

    def filter_candidates(self, *jsonl_files, out_file, excel_file, col_name='FacultyPage'):
        """
        filter candidates from jsonl files

        :param jsonl_files: list of str
            The jsonl files that contains faculty members
        :param out_file: str
            The output file to save the candidates
        :param excel_file: str
            The excel file that contains urls
        :param col_name: str
            The column name that contains urls
        """
        with open(excel_file, 'rb') as f:
            df = pd.read_excel(f)
        candidates = []
        for jsonl_file in expand_globs(jsonl_files):
            with open(jsonl_file, 'r', encoding='utf-8') as fp:
                basename = os.path.basename(jsonl_file)
                row = df[df[col_name].apply(
                    lambda x: isinstance(x, str) and basename.startswith(url_to_filename(x))
                )]
                for data in jsonl_load(fp):
                    data = dict_ignore_none(data)
                    faculty = FacultyMember(**data)
                    if not row.empty:
                        faculty.institute = row['Institute'].values[0]
                        faculty.department = row['Department'].values[0]
                        if not faculty.profile_url.startswith('http'):
                            base_url: str = row[col_name].values[0]
                            # remove query string from base url
                            base_url = base_url.split('?', maxsplit=1)[0]
                            if faculty.profile_url.startswith('/'):
                                # remove path from base url
                                base_url = base_url[:8] + base_url[8:].split('/', maxsplit=1)[0]
                            faculty.profile_url = base_url + faculty.profile_url
                    title = faculty.title.lower()
                    if not title:
                        logger.warning(f'title is empty for {faculty.name} in {jsonl_file}')
                    if 'assist' in title and 'prof' in title:
                        candidates.append(faculty.model_dump())

        df = pd.DataFrame(candidates)
        with open(out_file, 'wb') as f:
            df.to_excel(f, index=False)

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
                    logger.info(f'skip {url} as {out_file} already exists')
                    continue
                logger.info(f'scraping {url}')
                await page.goto(url)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(1)
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(await page.content())

    def _get_open_ai_client(self):
        base_url = config.get('openai_base_url')
        api_key = config.get('openai_api_key')
        client = OpenAI(base_url=base_url, api_key=api_key)
        return client

    def _get_open_ai_response(self, client: OpenAI, prompt, text):
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': text},
        ]
        res = client.chat.completions.create(
            model='deepseek-chat',
            messages=messages,  # type: ignore
            stream=False,
            max_tokens=4096 * 2,
        )
        with open(self._openai_log, 'a', encoding='utf-8') as f:
            json.dump(res.model_dump(), f)
        return res

    def _load_context(self, excel_file):
        import pandas as pd
        with open(excel_file, 'rb') as f:
            return pd.read_excel(f)


class FacultyMember(BaseModel):
    name: str
    title: str = ''
    email: str = ''
    introduction: str = ''
    institute: str = ''
    department: str = ''
    profile_url: str = ''
