import pytest
import localization


_TEST_KEY = 'dota2'
_TEST_BAD_KEY = 'bad_key_not_existing124'


def test_non_existing_locale():
    assert localization.get(_TEST_KEY, 'hy_AM') == localization.get(_TEST_KEY, None)
    assert localization.get(_TEST_KEY, '1241') == localization.get(_TEST_KEY, None)


def test_shorter_locale():
    assert localization.get(_TEST_KEY, 'en') == localization.get(_TEST_KEY, 'en_US')
    assert localization.get(_TEST_KEY, 'ru') == localization.get(_TEST_KEY, 'ru_RU')


def test_non_existing_key():
    with pytest.raises(KeyError):
        localization.get(_TEST_BAD_KEY)
