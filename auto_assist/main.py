from typing import Optional
from ruamel.yaml import YAML
from playwright.async_api import async_playwright

import asyncio
import os
import fire

from .browser import lauch_browser
from .lib import USER_HOME



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
        return BrowserCmd(self.config.get('browsers', {}))


class BrowserCmd:

    def __init__(self, config: dict) -> None:
        self.config = config

    def launch(self, name: str = 'default'):
        config = self.config.get(name, {})
        async def _launch():
            async with async_playwright() as pw:
                await lauch_browser(name, config, USER_HOME)(pw)
                input('Press any key to exit ...')
        asyncio.run(_launch())


if __name__ == '__main__':
    fire.Fire(Entry)