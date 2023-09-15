from typing import Dict, Optional
from playwright.async_api import Playwright, BrowserContext
import os

from .lib import USER_HOME

def lauch_browser(name: str = 'default',
                  config: Optional[dict] = None,
                  user_home: str = USER_HOME):
    if config is None:
        config = {}

    config = {
        'channel': 'chrome',
        'user_data_dir': os.path.join(user_home,'user-data', name),
        'downloads_path': './my-downloads',
        'headless': False,
        'ignore_https_errors': True,
        'ignore_default_args': [
            '--enable-automation',
            '--no-sandbox',
            '--disable-extensions',
            '--disable-background-networking',
        ],
        **config,
    }

    async def _launcher(pw: Playwright):
        for key in ['user_data_dir', 'downloads_path']:
            dir_path = config.get(key)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        return await pw.chromium.launch_persistent_context(**config)

    return _launcher
