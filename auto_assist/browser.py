from typing import Dict
from playwright.async_api import Playwright, BrowserContext

import os


class BrowserManager:

    def __init__(self, pw: Playwright, user_home: str) -> None:
        self.pw = pw
        self.browsers:Dict[str, BrowserContext] = {}
        self.config = {}
        self.user_home = user_home

    def get_user_path(self, *args):
        return os.path.join(self.user_home, *args)

    def get_config(self, name: str):
        config = {
            'channel': 'chrome',
            'user_data_dir': self.get_user_path('user-data', name),
            'downloads_path': './auto-assit-downloads',
            'headless': False,
            'ignore_https_errors': True,
            'ignore_default_args': [
                '--enable-automation',
                '--no-sandbox',
                '--disable-extensions',
            ],
            **self.config.get(name, {}),
        }
        return config

    async def get_browser(self, name: str) -> BrowserContext:
        if name not in self.browsers:
            config = self.get_config(name)
            init_browser(config)
            self.browsers[name] = await self.pw.chromium.launch_persistent_context(**config)
        return self.browsers[name]


def init_browser(config: dict):
    for key in ['user_data_dir', 'downloads_path']:
        dir_path = config.get(key)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
