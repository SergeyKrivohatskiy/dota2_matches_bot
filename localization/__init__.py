import plate
import os

_locales_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'locales')
_plate = plate.Plate(root=_locales_dir, locale='en_US', fallback='en_US')


def get(string_key, locale=None, **parameters):
    if locale is None or locale in _plate.locales:
        return _plate(string_key, locale, **parameters)
    return get(string_key, None, **parameters)
