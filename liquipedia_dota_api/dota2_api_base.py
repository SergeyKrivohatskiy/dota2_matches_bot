import requests
import urllib.request
import bs4
import time
import typing
from liquipedia_dota_api.exceptions import RequestsException
from liquipedia_dota_api.config import LIQUIPEDIA_URL

__all__ = ['Dota2ApiBase']


def _get_as_soup(url, headers):
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise RequestsException(response.json(), response.status_code)

    try:
        page_html = response.json()['parse']['text']['*']
    except KeyError:
        raise RequestsException(response.json(), response.status_code)

    return bs4.BeautifulSoup(page_html, features='lxml')


def _time():
    if hasattr(time, 'monotonic'):
        return time.monotonic
    return time.time


class Dota2ApiBase:
    def __init__(self, app_name: str, parse_period: float, get_period: float):
        self._headers = {'User-Agent': app_name, 'Accept-Encoding': 'gzip'}
        self._base_url = LIQUIPEDIA_URL + '/dota2/api.php?'

        self._time = _time()
        self._parse_period = parse_period
        self._last_parse = self._time() - self._parse_period
        self._get_period = get_period
        self._last_get = self._time() - self._get_period

    def parse(self, page: str) -> typing.Tuple[bs4.BeautifulSoup, typing.Optional[str]]:
        to_wait = self._last_parse + self._parse_period - self._time()
        if to_wait > 0:
            time.sleep(to_wait)
        self._last_parse = self._time()

        return self._parse_impl(page)

    def get(self, page: str):
        to_wait = self._last_get + self._get_period - self._time()
        if to_wait > 0:
            time.sleep(to_wait)
        self._last_get = self._time()

        return self._get_impl(page)

    def _parse_impl(self, page):
        soup = _get_as_soup(self._base_url + 'action=parse&format=json&page=' + page, self._headers)

        redirect = soup.find('ul', class_='redirectText')
        if redirect is None:
            return soup, None

        redirect_url = soup.find('a').get_text()
        redirect_url = urllib.request.quote(redirect_url)
        soup, _ = self._parse_impl(redirect_url)

        return soup, redirect_url

    @staticmethod
    def _get_impl(page):
        assert(page.startswith('/'))
        r = requests.get(LIQUIPEDIA_URL + page)
        return r.content
