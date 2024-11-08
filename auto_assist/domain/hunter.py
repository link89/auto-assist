from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel

from typing import List
import subprocess as sp
import requests
import asyncio
import json
import os

from auto_assist.lib import url_to_filename, expand_globs, get_logger, get_md_code_block
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
                data = next(get_md_code_block(res.choices[0].message.content, '```json')).strip()
                with open(data_file, 'w', encoding='utf-8') as f:
                    f.write(data)
            except Exception as e:
                logger.exception(f'fail to retrive faculty members from {md_file}')


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

    def _ensure_valid_json(self, client:OpenAI, text: str, pydantic_model, max_treis=3):
        origin_text = text
        for _ in range(max_treis):
            try:
                obj = json.loads(text)
                pydantic_model.parse_obj(obj)
                return json.dumps(obj)
            except Exception as e:
                logger.error(f'invalid json: {origin_text}, try to fix: {e}')
                # always use the original text to fix
                res = self._get_open_ai_response(client, prompt.FIX_FACULTY_JSON, origin_text)
                text = next(get_md_code_block(res.choices[0].message.content, '```json')).strip()
        logger.error(f'Can not fix the json string: {origin_text}')
        raise ValueError('Fail to fix broken json string')


class FacultyMember(BaseModel):
    name: str
    title: str = ''
    email: str = ''
    institue: str = ''
    department: str = ''
    introduction: str = ''
    profile_url: str = ''
    avarar_url: str = ''


def _get_urls(file):
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


