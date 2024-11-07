import fire

from .browser import BrowserCmd
from .domain.google_scholar import GsCmd
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