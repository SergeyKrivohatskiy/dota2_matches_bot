import threading
import telegram
import logging
import peewee
import telegram_bot.config as config


_logger = logging.getLogger('settings_storage')


_db = peewee.SqliteDatabase(
    config.SETTINGS_STORAGE_FILE,
    pragmas={
        'journal_mode': 'wal',
        'cache_size': -1 * 64000,
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 0})


class _BaseModel(peewee.Model):
    class Meta:
        database = _db


class _ChatSetting(_BaseModel):
    chat_id = peewee.CharField(unique=True)
    setting_key = peewee.CharField(unique=True)
    setting_value = peewee.CharField(unique=True)


class SettingsStorage:
    def __init__(self):
        self._lock = threading.Lock()
        _logger.info('connecting db')
        _db.connect()
        _logger.info('creating tables')
        _db.create_tables([_ChatSetting])

    def get(self, chat_id: str, key: str, default=None):
        with self._lock:
            q = _ChatSetting.select().where((_ChatSetting.chat_id == chat_id) & (_ChatSetting.setting_key == key))
            if q.count() == 0:
                return default
            return q[0].setting_value

    def set(self, chat_id: str, key, value):
        with self._lock:
            chat_setting, created = \
                _ChatSetting.get_or_create(chat_id=chat_id, setting_key=key, defaults={'setting_value': value})
            if created:
                return
            chat_setting.setting_value = value
            chat_setting.update().execute()


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
