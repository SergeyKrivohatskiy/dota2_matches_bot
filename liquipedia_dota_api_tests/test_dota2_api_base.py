import pytest
import time
from liquipedia_dota_api.dota2_api_base import Dota2ApiBase
from liquipedia_dota_api.config import DEFAULT_PARSE_PERIOD, DEFAULT_GET_PERIOD


_APP_NAME = 'liquipedia Dota2ApiBase tests (sergey@krivohatskiy.com)'


def test_parse_and_period():
    api = Dota2ApiBase(app_name=_APP_NAME, parse_period=DEFAULT_PARSE_PERIOD, get_period=DEFAULT_GET_PERIOD)
    soup, redirect = api.parse('Portal:Teams')
    assert len(soup) != 0
    assert redirect is None

    first_request_finished = time.time()
    api.parse('Portal:Teams')
    time_passed = time.time() - first_request_finished
    assert pytest.approx(DEFAULT_PARSE_PERIOD, abs=5.0) == time_passed
