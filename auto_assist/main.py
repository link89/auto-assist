from typing import Optional, List
from ruamel.yaml import YAML
import asyncio
import fire
import sys

from .browser import BrowserCmd
from .lib import USER_HOME, pending
from .domain import google_scholar as gs
from .domain.hunter import ChemistryHunterCmd


class MainCmd:
    def browser(self):
        return BrowserCmd

    def gs(self):
        return GsCmd

    def ch(self):
        return ChemistryHunterCmd



if __name__ == '__main__':
    fire.Fire(MainCmd)