import fire

from .config import ConfigCmd
from .browser import BrowserCmd
from .domain.google_scholar import GsCmd
from .domain.hunter import HunterCmd


class MainCmd:
    def config(self):
        return ConfigCmd

    def browser(self):
        return BrowserCmd

    def gs(self):
        return GsCmd

    def hunter(self):
        return HunterCmd


def main():
    fire.Fire(MainCmd)
