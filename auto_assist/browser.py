from typing import Literal, Optional
from playwright.async_api import async_playwright, Playwright, BrowserContext

import asyncio
import os


USER_HOME = os.path.expanduser("~")



class BrowserManager:

    def __init__(self, pw: Playwright) -> None:
        self.pw = pw
        self.browser: Optional[BrowserContext] = None
        self.configs = {}

    def get_default_config(self):
        return {
            'channel': 'msedge',
            'user_data_dir': None,
            'downloads_path': './enoch-downloads',
            'headless': False,
            'ignore_https_error': True,
        }

    def config_browser(self,
                       name: str,
                       channel: str = 'msedge',
                       user_data_dir: Optional[str] = None,
                       downloads_path: str = './enoch-downloads',
                       headless = False,
                       ignore_https_error = True,
                       **kwargs,
                       ):
        self.configs[name] = {
            'channel': channel,
            'user_data_dir': user_data_dir,
            'downloads_path': downloads_path,
            'headless': headless,
            'ignore_https_error': ignore_https_error,
            **kwargs,
        }


    async def get_browser(self,
                          channel: str = 'msedge',
                          user_data_dir: Optional[str] = None,
                          downloads_path: str = './enoch-downloads',
                          headless = False,
                          ignore_https_error = True,
                          **kwargs,
                          ) -> BrowserContext:
        if self.browser is not None:
            return self.browser

        if user_data_dir is None:
            user_data_dir = os.path.join(USER_HOME, '.enoch', 'user-data', channel)
        os.makedirs(user_data_dir, exist_ok=True)
        os.makedirs(downloads_path, exist_ok=True)

        self.browser = await self.pw.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel=channel,
            downloads_path=downloads_path,
            headless=headless,
            ignore_https_errors=ignore_https_error,
            **kwargs,
        )
        return self.browser


async def main():
    async with async_playwright() as p:
        bm = BrowserManager(p)
        browser = await bm.get_browser()
        page = await browser.new_page()
        page.goto('https://www.google.com')
        input("Press Enter to continue...")

if __name__ == '__main__':
    asyncio.run(main())

