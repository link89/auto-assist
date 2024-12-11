from playwright.async_api import async_playwright, Page
from openai import OpenAI
from pprint import pprint

import pandas as pd
import subprocess as sp
import requests
import asyncio
import random
import json
import time
import os

from auto_assist.lib import (
    url_to_key, get_md_code_block, excel_autowidth,
    expand_globs, get_logger, clean_html, formal_filename,
    jsonl_load, jsonl_dump, jsonl_loads,
    json_load_file, json_dump_file,
    )
from auto_assist.browser import launch_browser
from auto_assist import config

from . import prompt

logger = get_logger(__name__)

class HunterCmd:

    def __init__(self,
                 pandoc_cmd='pandoc',
                 pandoc_opt='+RTS -M1024m -RTS --sandbox -f html-native_divs-native_spans -t markdown',
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

    def search_faculties(self, in_excel, out_dir, parse=False, max_tries=3, delay=1):
        """
        Search faculty members from excel file

        :param in_excel: str
            The input excel file that contains faculty information
        :param out_dir: str
            The output directory to save the faculty members
        :param parse: bool
            Whether to parse the faculty members
        """
        df = self.load_excel(in_excel)
        async def _run():
            async with async_playwright() as pw:
                # setup browser
                assert isinstance(self._browser_dir, str)
                browser = await launch_browser(self._browser_dir)(pw)
                page = browser.pages[0]
                await page.route('**/*.{png,jpg,jpeg,webp,css,woff,woff2,ttf,svg}', lambda route: route.abort())
                for i, row in df.iterrows():
                    await self._async_search_faculty(row, out_dir, page, parse=parse)
        asyncio.run(_run())

        for _ in range(max_tries):
            try:
                asyncio.run(_run())
                logger.info('search faculties done')
                break
            except Exception as e:
                logger.exception(f'fail to search faculties')
                time.sleep(delay)

    def process_faculties(self, *faculty_dirs, out_excel):
        """
        filter candidates from jsonl files

        :param faculty_dirs: list of str
            The faculty directories that contains faculty members
        :param out_excel: str
            The output excel file to save the candidates
        """
        candidates = []
        for faculty_dir in expand_globs(faculty_dirs):
            index_json_file = os.path.join(faculty_dir, 'index.json')
            index = json_load_file(index_json_file)
            faculty_json_file = os.path.join(faculty_dir, 'faculty.html.md.jsonl')
            with open(faculty_json_file, 'r', encoding='utf-8') as f:
                faculties = list(jsonl_load(f))
            base_url = index.get('FacultyPage', '')
            base_url = base_url.split('?', maxsplit=1)[0]  # remove query string
            assert isinstance(base_url, str), f'invalid base url: {base_url}'
            for faculty in faculties:
                faculty['src'] = index['FacultyPage']
                faculty['institute'] = index.get('Institute', '')
                faculty['department'] = index.get('Department', '')
                profile_url = faculty.get('profile_url', '')
                if profile_url and not profile_url.startswith('http'):
                    _base_url = base_url
                    if profile_url.startswith('/'):
                        _base_url = base_url[:8] + base_url[8:].split('/', maxsplit=1)[0]
                    faculty['profile_url'] = _base_url + profile_url
                title = faculty.get('title', '').lower()
                if not title:
                    logger.warning(f'title is empty for {faculty["name"]} in {faculty_json_file}')
                if ('assist' in title and 'prof' in title) or ('aprof' in title):
                    candidates.append(faculty)

        df = pd.DataFrame(candidates)
        with open(out_excel, 'wb') as f:
            df.to_excel(f, index=False)

    def search_cvs(self, in_excel, out_dir, max_search=3, max_tries=1, delay=1, parse=False):
        df = self.load_excel(in_excel)
        async def _run():
            async with async_playwright() as pw:
                # setup browser
                assert isinstance(self._browser_dir, str)
                browser = await launch_browser(self._browser_dir)(pw)
                page = browser.pages[0]
                await page.route('**/*.{png,jpg,jpeg,webp,css,woff,woff2,ttf,svg}', lambda route: route.abort())
                for i, row in df.iterrows():
                    await self._async_search_cv(row, out_dir, page,
                                                max_search=max_search, parse=parse)
        for _ in range(max_tries):
            try:
                asyncio.run(_run())
                logger.info('search cvs done')
                break
            except Exception as e:
                logger.exception(f'fail to search cvs')
                time.sleep(delay)

    def process_cvs(self, *cv_dirs, out_excel):
        """
        filter teams from json files

        :param cv_dirs: list of str
            The cv directories that contains cv information
        :param out_file: str
            The output file in excel format to save the teams
        """
        groups = []

        for cv_dir in expand_globs(cv_dirs):
            cv_file_pattern = os.path.join(cv_dir, 'cv-*.json')
            for cv_file in expand_globs([cv_file_pattern]):
                cv = json_load_file(cv_file)
                member = cv.get('name', '')
                if not member:
                    continue
                email = cv.get('email', '')
                for exp in cv.get('experiences', []):
                    advisor = exp.get('advisor', '')
                    if not advisor:
                        continue
                    group = {
                        'member': member,
                        'email': email,
                        'title': exp.get('title', ''),
                        'institute': exp.get('institute', ''),
                        'group': exp.get('group', ''),
                        'advisor': advisor,
                    }
                    groups.append(group)

        with open(out_excel, 'wb') as f:
            df = pd.DataFrame(groups)
            with pd.ExcelWriter(f, engine_kwargs={'options': {'strings_to_urls': False}}) as writer:
                df.to_excel(writer, sheet_name='groups', index=False)
                excel_autowidth(df, writer.sheets['groups'], max_width=150)

    def search_group_members(self, in_excel, out_dir, max_search=3, max_tries=1, delay=1, parse=False):
        """
        Search group members from excel file

        :param in_excel: str
            The input excel file that contains advisor and group information
        :param out_dir: str
        """
        df = self.load_excel(in_excel)
        async def _run():
            async with async_playwright() as pw:
                # setup browser
                assert isinstance(self._browser_dir, str)
                browser = await launch_browser(self._browser_dir)(pw)
                page = browser.pages[0]
                await page.route('**/*.{png,jpg,jpeg,webp,css,woff,woff2,ttf,svg}',
                                 lambda route: route.abort())
                # search team members
                known_advisors = set()

                for i, row in df.iterrows():
                    advisor = row.get('advisor')
                    if not isinstance(advisor, str) or not advisor or advisor.lower() in known_advisors:
                        continue
                    known_advisors.add(advisor.lower())
                    await self._async_search_group(row, out_dir, page,
                                                   max_search=max_search, parse=parse)

        for _ in range(max_tries):
            try:
                asyncio.run(_run())
                logger.info('search team members done')
                break
            except Exception as e:
                logger.exception(f'fail to search team members')
                time.sleep(delay)

    def process_groups(self, *group_dirs, out_excel):
        """
        Filter group members from group directories

        :param group_dirs: list of str
            The group directories that contains group members
        :param out_excel: str
            The output excel file to save the group members
        """
        groups = []
        candidates = []

        known_names = set()
        for group_dir in expand_globs(group_dirs):
            index_json_file = os.path.join(group_dir, 'index.json')
            group = json_load_file(index_json_file)
            google_search_file = os.path.join(group_dir, 'google-search.json')
            google_results = json_load_file(google_search_file)
            urls = [r['url'] for r in google_results if valid_group_url(r['url'])][:3]

            groups.append({
                'institute': group.get('institute', ''),
                'group': group.get('group', ''),
                'advisor': group.get('advisor', ''),
                'urls': '\r\n'.join(urls),
            })

            for group_file in expand_globs([f'{group_dir}\group-*.jsonl']):
                with open(group_file, 'r', encoding='utf-8') as f:
                    members = list(jsonl_load(f))

                for member in members:
                    try:
                        name = member.get('name', '')
                        if name.lower() in known_names:
                            continue
                        known_names.add(name.lower())
                        is_chinese = member.get('is_chinese', False)
                        if not is_chinese:
                            continue

                        title = member.get('title', '')
                        if not is_graduate(title):
                            continue

                        candidates.append({
                            'name': name,
                            'title': title,
                            'email': member.get('email', ''),
                            'group': group.get('group', ''),
                            'advisor': group.get('advisor', ''),
                            'institute': group.get('institute', ''),
                            'description': member.get('description', ''),
                        })
                    except Exception as e:
                        logger.exception(f'fail to process {group_file}')
                        logger.info(f'member: {member}')

        group_df = pd.DataFrame(groups)
        candidate_df = pd.DataFrame(candidates)

        with pd.ExcelWriter(out_excel, engine_kwargs={'options':{'strings_to_urls': False}}) as writer:
            writer.book.formats[0].set_text_wrap()  # type: ignore
            group_df.to_excel(writer, sheet_name='groups', index=False)
            candidate_df.to_excel(writer, sheet_name='candidates', index=False)

            excel_autowidth(group_df, writer.sheets['groups'], max_width=150)
            excel_autowidth(candidate_df, writer.sheets['candidates'], max_width=150)

    def google_search(self, keyword: str, debug=False):
        async def _run():
            async with async_playwright() as pw:
                assert isinstance(self._browser_dir, str)
                browser = await launch_browser(self._browser_dir)(pw)
                page = browser.pages[0]
                await page.route('**/*.{png,jpg,jpeg,webp,css,woff,woff2,ttf,svg}', lambda route: route.abort())
                links = await self._async_google_search(keyword, page)
                if debug:
                    pprint(links)
                    input('press any key to continue')
                return links
        links = asyncio.run(_run())
        return links

    def pandoc_convert(self, in_html, out_md):
        """
        Convert html to markdown

        :param in_html: str
            The input html file
        :param out_md: str
            The output markdown file
        """
        return sp.check_call(f'{self._pancdo_cmd} {self._pandoc_opt} "{in_html}" -o "{out_md}"', shell=True)

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
            self.pandoc_convert(in_file, out_file)

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
            with open(in_file, 'r+', encoding='utf-8') as f:
                cleaned = clean_html(f)
                f.seek(0)
                f.write(cleaned)

    async def _async_search_faculty(self, faculty: pd.Series, out_dir, page: Page, parse=False):
        """
        Extract faculty member information from web page
        """
        url = faculty['FacultyPage']
        if not isinstance(url, str) or not url:
            return
        key = url_to_key(url, no_ext=True)
        faculty_dir = os.path.join(out_dir, key)
        os.makedirs(faculty_dir, exist_ok=True)

        # dump index.json
        index_file = os.path.join(faculty_dir, 'index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(faculty.to_json())

        # scrape faculty page
        faculty_html_file = os.path.join(faculty_dir, 'faculty.html')
        faculty_md_file = faculty_html_file + '.md'
        faculty_jsonl_file = faculty_md_file + '.jsonl'

        if not os.path.exists(faculty_html_file):
            html = await self._async_scrape_url(url, page)
            html = clean_html(html, keep_attrs=True)
            with open(faculty_html_file, 'w', encoding='utf-8') as f:
                f.write(html)

        if not os.path.exists(faculty_md_file):
            self.pandoc_convert(faculty_html_file, faculty_md_file)

        # parse faculty page
        if not parse or os.path.exists(faculty_jsonl_file):
            return

        with open(faculty_md_file, 'r', encoding='utf-8') as f:
            faculty_md_content = f.read()

        answer = ''
        try:
            res = self._get_open_ai_response(
                client=self._get_open_ai_client(),
                prompt=prompt.RETRIVE_FACULTY_MEMBERS,
                text='\n'.join([
                    'Markdown: """',
                    faculty_md_content,
                    '"""',
                ])
            )
            answer = res.choices[0].message.content
            data = next(get_md_code_block(answer, '```json')).strip()
            obj = jsonl_loads(data)
            with open(faculty_jsonl_file, 'w', encoding='utf-8') as f:
                jsonl_dump(f, obj)
        except Exception as e:
            logger.exception(f'fail to parse json data: {faculty_md_file}')
            logger.info(f'answer: {answer}')

    async def _async_search_cv(self, profile: pd.Series, out_dir, page: Page,
                               max_search=3, profile_url=None, parse=False):
        name = profile['name']
        institute = profile['institute']
        key = formal_filename(f'{name}-{institute}')

        cv_dir = os.path.join(out_dir, key)
        os.makedirs(cv_dir, exist_ok=True)
        # dump index.json
        index_file = os.path.join(cv_dir, 'index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(profile.to_json())

        # run google search
        gs_result_file = os.path.join(cv_dir, f'google-search.json')
        search_keyword = f'professor {name} {institute} (CV or resume or homepage or profile)'

        if not os.path.exists(gs_result_file):
            gs_results = await self._async_google_search(search_keyword, page)
            json_dump_file(gs_results, gs_result_file)
        else:
            gs_results = json_load_file(gs_result_file)

        # retrive data from web page
        urls = [r['url'] for r in gs_results if valid_cv_url(r['url'])][:max_search]
        if profile_url:
            urls.append(profile_url)

        for url in urls:
            # scrape cv html
            filename = url_to_key(url)
            cv_html_file = os.path.join(cv_dir, f'cv-{filename}')
            cv_md_file = cv_html_file + '.md'
            cv_json_file = cv_md_file + '.json'

            if not os.path.exists(cv_html_file):
                cv_html = await self._async_scrape_url(url, page)
                cv_html = clean_html(cv_html)
                with open(cv_html_file, 'w', encoding='utf-8') as f:
                    f.write(cv_html)

            if not os.path.exists(cv_md_file):
                self.pandoc_convert(cv_html_file, cv_md_file)

            # parse cv
            if not parse or os.path.exists(cv_json_file):
                continue

            with open(cv_md_file, 'r', encoding='utf-8') as f:
                cv_md_content = f.read()
            answer = ''
            try:
                res = self._get_open_ai_response(
                    client=self._get_open_ai_client(),
                    prompt=prompt.RETRIEVE_SCHOLAR_OBJECT,
                    text='\n'.join([
                        'Markdown: """',
                        cv_md_content,
                        '"""',
                    ])
                )
                answer = res.choices[0].message.content
                data = next(get_md_code_block(answer, '```json')).strip()
                obj = json.loads(data)
                json_dump_file(obj, cv_json_file)
            except Exception as e:
                logger.exception(f'fail to parse json data: {cv_md_file}')
                logger.info(f'answer: {answer}')
                continue

    async def _async_search_group(self, group: pd.Series, out_dir, page: Page,
                                  max_search=3, parse=False):
        advisor = group['advisor']
        institute = group['institute']
        key = formal_filename(f'{advisor}-{institute}')

        group_dir = os.path.join(out_dir, key)
        os.makedirs(group_dir, exist_ok=True)

        # dump index.json
        index_file = os.path.join(group_dir, 'index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(group.to_json())

        # google search
        gs_search_file = os.path.join(group_dir, 'google-search.json')
        search_keywords = f'(research group of {advisor}) AND (members or people) AND (graduate or phd or postdoctoral) {institute}'
        if not os.path.exists(gs_search_file):
            gs_results = await self._async_google_search(search_keywords, page)
            json_dump_file(gs_results, gs_search_file)
        else:
            gs_results = json_load_file(gs_search_file)

        # sort the results by if member in the title or snippet
        gs_results = sorted(gs_results, reverse=True, key=score_group_search)
        urls = [r['url'] for r in gs_results if valid_group_url(r['url'])][:max_search]
        for url in urls:
            filename = url_to_key(url)
            group_html_file = os.path.join(group_dir, f'group-{filename}')
            group_md_file = group_html_file + '.md'
            group_jsonl_file = group_md_file + '.jsonl'

            if not os.path.exists(group_html_file):
                group_html = await self._async_scrape_url(url, page)
                group_html = clean_html(group_html)
                with open(group_html_file, 'w', encoding='utf-8') as f:
                    f.write(group_html)

            if not os.path.exists(group_md_file):
                self.pandoc_convert(group_html_file, group_md_file)

            # parse group members
            if not parse or os.path.exists(group_jsonl_file):
                continue

            with open(group_md_file, 'r', encoding='utf-8') as f:
                group_md_content = f.read()

            answer = ''
            try:
                res = self._get_open_ai_response(
                    client=self._get_open_ai_client(),
                    prompt=prompt.RETRIVE_GROUP_MEMBERS,
                    text='\n'.join([
                        'Markdown: """',
                        group_md_content,
                        '"""',
                    ]),
                )
                answer = res.choices[0].message.content
                data = next(get_md_code_block(answer, '```json')).strip()
                if not data:
                    logger.warning(f'no data found for {group_md_file}')
                    continue
                # check if the data is valid jsonl
                members = jsonl_loads(data)
                with open(group_jsonl_file, 'w', encoding='utf-8') as f:
                    jsonl_dump(f, members)
            except Exception as e:
                logger.exception(f'fail to parse json data: {group_md_file}')
                logger.info(f'answer: {answer}')
                continue

    async def _async_google_search(self, keyword: str, page: Page):
        await page.goto('https://www.google.com/ncr')
        # add some random delay and mouse move to avoid bot detection
        random_xy_seq = [(random.uniform(100, 500), random.uniform(100, 500))
                         for _ in range(random.randint(3, 5))]
        for x, y in random_xy_seq:
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.2))
        await page.click('textarea[name="q"]')
        await page.fill('textarea[name="q"]', keyword)
        await page.press('textarea[name="q"]', 'Enter')
        await page.wait_for_selector('div#search div.g[jscontroller][jsaction]')
        result = await page.evaluate(
            '''() => Array.from(document.querySelectorAll('div#search div.g[jscontroller][jsaction]')).map(e => ({
            title: e.querySelector('h3')?.innerText,
            url: e.querySelector('a')?.href,
            snippet: e.querySelector('span')?.innerText
        }))''')
        return result

    def _requests_get(self, url):
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0 '
        if self._proxy:
            proxies = {
                'http': self._proxy,
                'https': self._proxy,
            }
        else:
            proxies = None
        return requests.get(url, proxies=proxies, headers={'User-Agent': user_agent})

    async def _async_scrape_url(self, url, page: Page, delay=0.5):
        await page.goto(url, timeout=60e3)
        await page.wait_for_load_state('domcontentloaded')
        if delay > 0:
            await asyncio.sleep(delay)
        # if there is cloudflare protection, try to solve it
        # detect cloudflare protection
        title = await page.title()
        if 'just a moment' in title.lower():
            await asyncio.sleep(10)
        content = await page.content()
        return content

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

    def load_excel(self, excel_file):
        import pandas as pd
        with open(excel_file, 'rb') as f:
            return pd.read_excel(f)


def is_graduate(title: str):
    title = title.lower()
    for keyword in ['phd', 'doctor', 'ph.d', 'post']:
        if keyword in title:
            return True
    if 'graduate' in title and 'under' not in title:
        return True
    return False


def valid_cv_url(url):
    if '.pdf' in url:
        return False
    if 'scholar.google' in url:
        return False
    return True


def valid_group_url(url):
    if '.pdf' in url:
        return False
    if is_personal_page(url):
        return False
    return True


def score_group_search(result):
    """
    Score the search result for filtering group members
    Tuning this have a big impact on the finial result
    """
    title = result['title'].lower()
    snippet = result['snippet'].lower()
    if 'member' in title or 'member' in snippet:
        return 10
    if 'graduate' in title or 'graduate' in snippet:
        return 7
    if 'people' in title or 'people' in snippet:
        return 5
    if 'profile' in title or 'profile' in snippet:
        return -5
    return 0


def is_personal_page(url):
    kws = [
        'linkedin', 'researchgate', 'scholar.google', 'wikipedia',
        'youtube', 'reddit', 'twitter', 'x.com', 'facebook', 'instagram',
        'github', 'gitlab', 'bitbucket', 'slides', 'frontiersin',
    ]
    return any(kw in url for kw in kws)
