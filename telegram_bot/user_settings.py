import threading


class SettingsStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = dict()

    def _check_user_exists(self, user_id):
        if user_id not in self._data:
            self._data[user_id] = dict()

    def get(self, user_id, key, default=None):
        with self._lock:
            self._check_user_exists(user_id)
            if key not in self._data[user_id]:
                return default
            return self._data[user_id][key]

    def set(self, user_id, key, value):
        with self._lock:
            self._check_user_exists(user_id)
            self._data[user_id][key] = value


_def_storage = SettingsStorage()


def storage() -> SettingsStorage:
    return _def_storage
