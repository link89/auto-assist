from typing import Optional, List
from ruamel.yaml import YAML
from playwright.async_api import async_playwright

from contextlib import asynccontextmanager
import asyncio
import os
import fire
import sys

from .browser import launch_browser
from .lib import USER_HOME, pending
from .tasks import google_scholar as gs


class MainCmd:
    def browser(self):
        return BrowserCmd()

    def task(self):
        return TaskCmd(self)


class BrowserCmd:

    def __init__(self):
        pass

    def launch(self, browser_dir: str, **kwargs):
        async def run():
            async with self._launch_async(browser_dir, **kwargs):
                input('Press any key to exit ...')
        asyncio.run(run())

    @asynccontextmanager
    async def _launch_async(self, browser_dir: str, **kwargs):
        async with async_playwright() as pw:
            yield await launch_browser(browser_dir, **kwargs)(pw)


class TaskCmd:

    def __init__(self, browser_dir) -> None:
        pass

    def gs_search_by_authors(self,
                             out_dir: str = './out',
                             page_limit=3,
                             keyword='',
                             google_scholar_url='https://scholar.google.com/?hl=en&as_sdt=0,5',
                             browser='default',
                             ):
        authors = [line.strip() for line in sys.stdin]
        async def run():
            async with self._entry.browser()._launch_async(browser) as browser_ctx:
                await gs.gs_search_by_authors(
                    browser_ctx, authors=authors, out_dir=out_dir, keyword=keyword, page_limit=page_limit, google_scholar_url=google_scholar_url)
                pending()
        asyncio.run(run())

    def gs_explore_profiles(self,
                            out_dir: str = './out',
                            depth_limit=1,
                            google_scholar_url='https://scholar.google.com/',
                            browser='default',
                            order_by_year=True,
                            ):
        profile_urls = [line.strip() for line in sys.stdin]
        async def run():
            async with self._entry.browser()._launch_async(browser) as browser_ctx:
                await gs.gs_explore_profiles(
                    browser_ctx, gs_profile_urls=profile_urls, out_dir=out_dir, depth_limit=depth_limit, order_by_year=order_by_year, google_scholar_url=google_scholar_url,
                )
                pending()
        asyncio.run(run())


    def gs_list_profile_urls(self, result_file: str):
        gs.gs_list_profile_urls(result_file)


    def gs_list_authors(self, result_file: str):
        gs.gs_list_authors(result_file)


    def gs_fix_profile_from_html(self, out_dir: str, suffix = None):
        gs.gs_fix_profile_from_html(out_dir, suffix)


if __name__ == '__main__':
    fire.Fire(MainCmd)