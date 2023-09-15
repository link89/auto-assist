from typing import Optional
from ruamel.yaml import YAML
from playwright.async_api import async_playwright

import asyncio
import os
import fire

from .browser import BrowserManager

USER_HOME = os.path.join(os.path.expanduser("~"), '.auto-assist')


class Entry:

    def __init__(self, config_file: Optional[str] = None) -> None:
        if config_file is None:
            config_file = os.path.join(USER_HOME, 'config.yml')
        if os.path.exists(config_file):
            yaml = YAML(typ='safe')
            with open(config_file) as f:
                self.config = yaml.load(f)
        else:
            self.config = {}

    def browser(self):
        return BrowserCmd(self.config.get('browser', {}))


class BrowserCmd:

    def __init__(self, config: dict) -> None:
        self.config = config

    def open(self, name: str = 'default'):
        asyncio.run(self._open(name))


    async def _open(self, name: str):
        async with async_playwright() as p:
            bm = BrowserManager(p, USER_HOME)
            await bm.get_browser(name)
            input('Press any key to exit ...')


if __name__ == '__main__':
    fire.Fire(Entry)