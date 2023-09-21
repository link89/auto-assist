from playwright.async_api import BrowserContext, TimeoutError
from typing import Any, List, TypedDict
from urllib.parse import urlparse
import os
import json

from auto_assist.lib import get_logger

logger = get_logger(__name__)


class Citation(TypedDict):
    type: str
    title: str
    authors: List[str]
    journal: str
    volume: str
    number: str
    pages: str
    year: str
    publisher: str


class GsProfileEntry(TypedDict):
    name: str
    url: str


class GsProfileItem(TypedDict):
    name: str
    url: str
    brief: str
    cited_stats: str
    co_authors: List['GsProfileItem']


class GsSearchItem(TypedDict):
    url: str
    citation: Citation
    profiles: List[GsProfileEntry]


async def gs_explore_profiles(browser: BrowserContext,
                              gs_profile_urls: List[str],
                              out_dir: str = './out',
                              level_limit=2,
                              google_scholar_url='https://scholar.google.com/',
                              ):

    os.makedirs(out_dir, exist_ok=True)
    gs_profiles_file = os.path.join(out_dir, 'gs_profiles.jsonl')




async def gs_search_by_authors(browser: BrowserContext,
                               authors: List[str],
                               out_dir: str = './out',
                               page_limit=3,
                               google_scholar_url='https://scholar.google.com/?hl=en&as_sdt=0,5',
                               ):
    """
    search by authors in google scholar
    """
    os.makedirs(out_dir, exist_ok=True)
    gs_result_file = os.path.join(out_dir, 'gs_result.jsonl')

    # load existed results
    gs_search_result = []
    if os.path.exists(gs_result_file):
        gs_search_result: List[GsSearchItem] = load_jsonl(gs_result_file)

    processed_articles = set(item['url'] for item in gs_search_result)

    gs_page = browser.pages[0]
    for author in authors:
        # search articles by auther
        await gs_page.goto(google_scholar_url)
        await gs_page.locator('input#gs_hdr_tsi').fill(f'author:"{author}"')
        await gs_page.locator('input#gs_hdr_tsi').press('Enter')

        for i_page in range(page_limit):
            if i_page > 0:
                try:
                    await gs_page.locator('td[align="left"]').click(timeout=10e3)
                except TimeoutError:
                    logger.warn('no more page to process')
                    break

            # iterate each article in google scholar,
            cite_modal = gs_page.locator('div#gs_cit')

            article_divs = await gs_page.locator('div.gs_r.gs_or.gs_scl').all()
            for article_div in article_divs:
                try:
                    article_url = await article_div.locator('h3.gs_rt a').get_attribute('href', timeout=10e3)
                    if article_url in processed_articles:
                        logger.info('article %s has been processed', article_url)
                        continue

                    # download and parse endnote citation
                    await article_div.locator('a.gs_or_cit').click()

                    async with gs_page.expect_download() as download_info:
                        await cite_modal.locator('a.gs_citi').get_by_text('EndNote').click()
                    download = await download_info.value
                    # close cite modal
                    await cite_modal.locator('a#gs_cit-x').click()

                    await download.save_as(download.suggested_filename)
                    with open(download.suggested_filename, 'r', encoding='utf-8') as fp:
                        cite_data = fp.read()

                    citation = parse_endnote(cite_data)
                    logger.info('citation: %s', citation)

                    # get authors with google scholar and the link to their profile
                    profile_links = await article_div.locator('div.gs_a a').all()
                    gs_profiles = []
                    for profile_link in profile_links:
                        gs_profile = GsProfileEntry()
                        gs_profile['name'] = await profile_link.inner_text()
                        gs_profile['url'] = await profile_link.get_attribute('href')
                        logger.info('gs_profile: %s', gs_profile)
                        gs_profiles.append(gs_profile)

                    gs_search_item = GsSearchItem(
                        url=article_url,
                        citation=citation,
                        profiles=gs_profiles,
                    )
                    gs_search_result.append(gs_search_item)

                    # write result to file
                    with open(gs_result_file, 'a', encoding='utf-8') as fp:
                        fp.write(json.dumps(gs_search_item, ensure_ascii=False))
                        fp.write('\n')

                    processed_articles.add(article_url)

                except TimeoutError as e:
                    logger.exception("unexpected error occured")


def list_gs_profile_urls(result_file: str):
    result: List[GsSearchItem] = load_jsonl(result_file)
    urls = set(profile['url'] for item in result for profile in item['profiles'])
    for url in urls:
        print(url)


def get_gs_profile_id(url: str):
    return urlparse(url).params['user']


def load_jsonl(file: str):
    result = []
    with open(file, 'r', encoding='utf-8') as fp:
        for line in fp:
            result.append(json.loads(line))
    return result


def parse_endnote(text: str):
    """
    Parse EndNote citation to python dict data
    Example of EndNote citation:

    %0 Journal Article
    %T Theoretical studies on anatase and less common TiO2 phases: bulk, surfaces, and nanomaterials
    %A De Angelis, Filippo
    %A Di Valentin, Cristiana
    %A Fantacci, Simona
    %A Vittadini, Andrea
    %A Selloni, Annabella
    %J Chemical reviews
    %V 114
    %N 19
    %P 9708-9753
    %@ 0009-2665
    %D 2014
    %I ACS Publications
    """

    citation = Citation()
    citation['authors'] = []
    for line in text.splitlines():
        if line.startswith('%'):
            key, value = line[1:].split(' ', 1)
            if key == '0':
                citation['type'] = value
            elif key == 'T':
                citation['title'] = value.strip()
            elif key == 'A':
                citation['authors'].append(value.strip())
            elif key == 'J':
                citation['journal'] = value
            elif key == 'V':
                citation['volume'] = value
            elif key == 'N':
                citation['number'] = value
            elif key == 'P':
                citation['pages'] = value
            elif key == 'D':
                citation['year'] = value
            elif key == 'I':
                citation['publisher'] = value
    return citation
