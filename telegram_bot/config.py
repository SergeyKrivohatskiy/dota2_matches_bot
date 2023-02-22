import os


def bot_token():
    return os.environ['TELEGRAM_BOT_TOKEN']


ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

LOG_FILE = os.path.join(ROOT_DIR, 'log.txt')

REMINDERS_CHECK_PERIOD_SECONDS = 60  # This should be less than REMINDERS_WINDOW_SECONDS not to skip reminders
REMINDERS_WINDOW_SECONDS = 600  # remind [10, 0] minutes before match

REMINDERS_STORAGE_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reminders.db')

SETTINGS_STORAGE_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.db')

ADMIN_USER_ID = int(os.environ['ADMIN_USER_ID'])

LINE_WIDTH = 45


CALLBACK_COMMANDS = {
    'follow_all': 'fa',
    'follow_team': 'fte',
    'follow_tournament': 'fto',
    'show_streams': 'ss',
    'settings_to_begin': 's tb',
    'settings_close': 's close',
    'settings_to_language': 's tl',
    'settings_change_lang': 's cl',
    'remove_team_reminder': 'rter',
    'remove_tournament_reminder': 'rtor'
}
