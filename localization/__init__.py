import plate
import os

_locales_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'locales')
_plate = plate.Plate(root=_locales_dir, locale='en_US', fallback='en_US')

_locale_convert = {'ru': 'ru_RU', 'en': 'en_US'}


def all_locales():
    return _locale_convert.keys()


def get(string_key, locale=None, **parameters):
    if locale is None or locale in _plate.locales:
        return _plate(string_key, locale, **parameters)
    if locale in _locale_convert:
        return _plate(string_key, _locale_convert[locale], **parameters)
    return get(string_key, None, **parameters)
