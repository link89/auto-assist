from playwright.async_api import Playwright
from playwright.async_api import async_playwright
from contextlib import asynccontextmanager

import asyncio
import json
import os


def launch_browser(browser_dir: str, channel='chrome', **kwargs):
    browser_dir = os.path.expanduser(browser_dir)
    config_file = os.path.join(browser_dir, 'config.json')

    if os.path.exists(config_file):
        print('loading config from {}'.format(config_file))
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {
            'channel': channel,
            'user_data_dir': os.path.abspath(os.path.join(browser_dir,'user-data')),
            'headless': False,
            'ignore_https_errors': True,
            'slow_mo': 1000,
            'ignore_default_args': [
                '--enable-automation',
                '--no-sandbox',
                '--disable-extensions',
                '--disable-background-networking',
            ],
        }
        os.makedirs(browser_dir, exist_ok=True)

    config.update(kwargs)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print('config saved to {}'.format(config_file))

    for key in ['user_data_dir', 'downloads_path']:
        dir_path = config.get(key)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

    async def _launcher(pw: Playwright):
        return await pw.chromium.launch_persistent_context(**config)
    return _launcher


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
