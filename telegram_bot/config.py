import os


BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

REMINDERS_CHECK_PERIOD_SECONDS = 60  # This should be less than REMINDERS_WINDOW_SECONDS not to skip reminders
REMINDERS_WINDOW_SECONDS = 600  # remind [10, 0] minutes before match

LINE_WIDTH = 45
