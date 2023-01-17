import threading
import telegram
import logging


_logger = logging.getLogger('settings_storage')


class SettingsStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = dict()

    def _check_chat_exists(self, chat_id):
        if chat_id not in self._data:
            self._data[chat_id] = dict()

    def get(self, chat_id: str, key: str, default=None):
        with self._lock:
            self._check_chat_exists(chat_id)
            if key not in self._data[chat_id]:
                return default
            return self._data[chat_id][key]

    def set(self, chat_id: str, key, value):
        with self._lock:
            self._check_chat_exists(chat_id)
            self._data[chat_id][key] = value


_def_storage = SettingsStorage()


def storage() -> SettingsStorage:
    return _def_storage


_LANG_KEY = 'language'


def get_lang_for_known_chat(chat_id):
    lang = storage().get(chat_id, _LANG_KEY)
    if lang is None:
        _logger.warning(f'there is no lang setting for chat {chat_id}, get lang with update should be called first')
    return lang


def get_lang(update: telegram.Update):
    lang = storage().get(str(update.effective_chat.id), _LANG_KEY)
    if lang is not None:
        return lang

    storage().set(str(update.effective_chat.id), _LANG_KEY, update.effective_user.language_code)
    return get_lang(update)
