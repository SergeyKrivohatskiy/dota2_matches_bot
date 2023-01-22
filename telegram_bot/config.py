import os


def bot_token():
    return os.environ['TELEGRAM_BOT_TOKEN']


ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')

REMINDERS_CHECK_PERIOD_SECONDS = 60  # This should be less than REMINDERS_WINDOW_SECONDS not to skip reminders
REMINDERS_WINDOW_SECONDS = 600  # remind [10, 0] minutes before match

REMINDERS_STORAGE_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reminders.db')

ADMIN_USER_ID = int(os.environ['ADMIN_USER_ID'])

LINE_WIDTH = 45
