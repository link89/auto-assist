from urllib.parse import urlparse
from typing import Iterable, List
from bs4 import BeautifulSoup

import logging
import glob
import json
import os
import re


USER_HOME = os.path.join(os.path.expanduser("~"))

# format to include timestamp and module
logging.basicConfig(format='%(asctime)s %(name)s: %(message)s', level=logging.INFO)


def get_logger(name=None):
    return logging.getLogger(name)


def pending():
    input('Press any key to exit ...')


def contain_chinese(text):
    return re.search('[\u4e00-\u9fa5]', text) is not None


def is_pinyin(word: str):
    # table of all valid pinyin without tone
    pinyin = ['a', 'o', 'e', 'er', 'ai', 'ao', 'ou', 'an', 'en', 'ang', 'eng', 'yi', 'ya', 'yao', 'ye', 'you', 'yan', 'yin', 'yang', 'ying', 'yong', 'wu', 'wa', 'wo', 'wai', 'wei', 'wan', 'wen', 'wang', 'weng', 'yu', 'yue', 'yuan', 'yun', 'ba', 'bo', 'bai', 'bei', 'bao', 'ban', 'ben', 'bang', 'beng', 'bi', 'biao', 'bie', 'bian', 'bin', 'bing', 'bu', 'pa', 'po', 'pai', 'pei', 'pao', 'pou', 'pan', 'pen', 'pang', 'peng', 'pi', 'piao', 'pie', 'pian', 'pin', 'ping', 'pu', 'ma', 'mo', 'me', 'mai', 'mei', 'mao', 'mou', 'man', 'men', 'mang', 'meng', 'mi', 'miao', 'mie', 'miu', 'mian', 'min', 'ming', 'mu', 'fa', 'fo', 'fei', 'fou', 'fan', 'fen', 'fang', 'feng', 'fu', 'da', 'de', 'dai', 'dei', 'dao', 'dou', 'dan', 'den', 'dang', 'deng', 'dong', 'di', 'diao', 'die', 'diu', 'dian', 'ding', 'du', 'duo', 'dui', 'duan', 'dun', 'ta', 'te', 'tai', 'tei', 'tao', 'tou', 'tan', 'tang', 'teng', 'tong', 'ti', 'tiao', 'tie', 'tian', 'ting', 'tu', 'tuo', 'tui', 'tuan', 'tun', 'na', 'ne', 'nai', 'nei', 'nao', 'nou', 'nan', 'nen', 'nang', 'neng', 'nong', 'ni', 'niao', 'nie', 'niu', 'nian', 'nin', 'niang', 'ning', 'nu', 'nuo', 'nuan', 'nv', 'nve', 'la', 'le', 'lai', 'lei', 'lao', 'lou', 'lan', 'lang', 'leng', 'long', 'li', 'lia', 'liao', 'lie', 'liu', 'lian', 'lin', 'liang', 'ling', 'lu', 'luo', 'luan', 'lun', 'lv', 'lve', 'ga', 'ge', 'gai', 'gei', 'gao', 'gou', 'gan', 'gen', 'gang', 'geng', 'gong', 'gu', 'gua', 'guo', 'guai', 'gui', 'guan', 'gun', 'guang', 'ka', 'ke', 'kai', 'kei', 'kao', 'kou', 'kan', 'ken', 'kang', 'keng', 'kong', 'ku', 'kua', 'kuo', 'kuai', 'kui', 'kuan', 'kun', 'kuang', 'ha', 'he', 'hai', 'hei', 'hao', 'hou', 'han', 'hen', 'hang', 'heng', 'hong', 'hu', 'hua', 'huo', 'huai', 'hui', 'huan', 'hun', 'huang', 'za', 'ze', 'zi', 'zai', 'zei', 'zao', 'zou', 'zan', 'zen', 'zang', 'zeng', 'zong', 'zu', 'zuo', 'zui', 'zuan', 'zun', 'ca', 'ce', 'ci', 'cai', 'cao', 'cou', 'can', 'cen', 'cang', 'ceng', 'cong', 'cu', 'cuo', 'cui', 'cuan', 'cun', 'sa', 'se', 'si', 'sai', 'sao', 'sou', 'san', 'sen', 'sang', 'seng', 'song', 'su', 'suo', 'sui', 'suan', 'sun', 'zha', 'zhe', 'zhi', 'zhai', 'zhei', 'zhao', 'zhou', 'zhan', 'zhen', 'zhang', 'zheng', 'zhong', 'zhu', 'zhua', 'zhuo', 'zhuai', 'zhui', 'zhuan', 'zhun', 'zhuang', 'cha', 'che', 'chi', 'chai', 'chao', 'chou', 'chan', 'chen', 'chang', 'cheng', 'chong', 'chu', 'chua', 'chuo', 'chuai', 'chui', 'chuan', 'chun', 'chuang', 'sha', 'she', 'shi', 'shai', 'shei', 'shao', 'shou', 'shan', 'shen', 'shang', 'sheng', 'shu', 'shua', 'shuo', 'shuai', 'shui', 'shuan', 'shun', 'shuang', 're', 'ri', 'rao', 'rou', 'ran', 'ren', 'rang', 'reng', 'rong', 'ru', 'rua', 'ruo', 'rui', 'ruan', 'run', 'ji', 'jia', 'jiao', 'jie', 'jiu', 'jian', 'jin', 'jiang', 'jing', 'jiong', 'ju', 'jue', 'juan', 'jun', 'qi', 'qia', 'qiao', 'qie', 'qiu', 'qian', 'qin', 'qiang', 'qing', 'qiong', 'qu', 'que', 'quan', 'qun', 'xi', 'xia', 'xiao', 'xie', 'xiu', 'xian', 'xin', 'xiang', 'xing', 'xiong', 'xu', 'xue', 'xuan', 'xun']
    return word.lower() in pinyin


def url_to_key(url: str, include_query=False, no_ext=False):
    """
    Convert url to a valid filename

    :param url: str
        The url to convert
    """
    parsed = urlparse(url)
    filename = parsed.path.replace('/', '_')
    if include_query:
        filename += parsed.query
    # if filename not have extension, add .html
    if not os.path.splitext(filename)[1] and not no_ext:
        filename += '.html'
    return parsed.netloc + filename


def expand_globs(patterns: Iterable[str], raise_invalid=False) -> List[str]:
    """
    Expand glob patterns in paths

    :param patterns: list of paths or glob patterns
    :param raise_invalid: if True, will raise error if no file found for a glob pattern
    :return: list of expanded paths
    """
    paths = []
    for pattern in patterns:
        result = glob.glob(pattern, recursive=True) if '*' in pattern else [pattern]
        if raise_invalid and len(result) == 0:
            raise FileNotFoundError(f'No file found for {pattern}')
        for p in result:
            if p not in paths:
                paths.append(p)
            else:
                print(f'path {p} already exists in the list')
    return paths


def get_md_code_block(md_text: str, start: str, end: str='```'):
    """
    Get the code block from markdown text by yieling the code block text

    :param md_text: str
        The markdown text
    :param code_block_start: str
        The start of code block, e.g. '```json'
    :param code_block_end: str
        The end of code block, e.g. '```'
    """
    while True:
        start_idx = md_text.find(start)
        if start_idx == -1:
            break
        # find the end of code block
        md_text = md_text[start_idx + len(start):]
        end_idx = md_text.find(end, start_idx)
        if end_idx == -1:
            break
        yield md_text[:end_idx]
        # remove the code block from the text
        md_text = md_text[end_idx + len(end):]


def jsonl_load(fp):
    for l in fp:
        yield json.loads(l)


def jsonl_dump(fp, data):
    lines = [json.dumps(d) for d in data]
    fp.write('\n'.join(lines))


def jsonl_loads(s):
    return [json.loads(l) for l in s.strip().split('\n')]


def json_load_file(path, encoding='utf-8'):
    with open(path, encoding=encoding) as f:
        return json.load(f)


def dict_ignore_none(d):
    return {k: v for k, v in d.items() if v is not None}


def ensure_dir(path):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def clean_html(markup, keep_alink=False):
    soup = BeautifulSoup(markup, 'html.parser')
    for tag in soup():
        attrs = tag.attrs.copy() if tag.attrs else []
        for attr in attrs:
            if keep_alink and tag.name == 'a' and attr == 'href':
                continue
            del tag[attr]
        if tag.name in ['script', 'style', 'noscript', 'svg', 'img', 'iframe']:
            tag.decompose()
    return str(soup)


def formal_filename(s):
    return re.sub(r'[\\/:*?"<>|]', '_', s)


def excel_autowidth(df, sheet, max_width=None):
    def width(s):
        s = s.strip()
        if not s:
            return 0
        w = max([len(str(x)) for x in s.splitlines()])
        if max_width is not None:
            w = min(w, max_width)
        return w

    for idx, col in enumerate(df):
        series = df[col]
        max_len = max((series.astype(str).map(width).max(), len(str(series.name)))) + 1
        sheet.set_column(idx, idx, max_len)