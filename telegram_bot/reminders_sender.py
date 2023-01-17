import telegram
import logging
import threading
import config
import datetime
import reminders_storage
import matches_data_loader
# import localization TODO


_logger = logging.getLogger('reminders_sender')


class RemindersSender:
    def __init__(self, check_period=config.REMINDERS_CHECK_PERIOD_SECONDS,
                 reminder_window=config.REMINDERS_WINDOW_SECONDS):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._check_period: int = check_period
        self._reminder_window = datetime.timedelta(seconds=reminder_window)
        self._last_reminded_match_start_time = datetime.datetime.now()
        self._bot = telegram.Bot(config.BOT_TOKEN)
        self._check_thread = threading.Thread(target=self._check_loop, daemon=True)

    def start(self):
        _logger.info('starting reminders sender')
        self._check_thread.start()

    def _check_loop(self):
        while True:
            self._check_reminders()
            if self._stop_event.wait(self._check_period):
                break

    def stop_check_loop(self):
        if self._stop_event.is_set():
            return
        _logger.info('Stopping reminders check')
        self._stop_event.set()
        self._check_thread.join()

    def _check_reminders(self):
        _logger.info('checking reminders')
        matches = matches_data_loader.get_matches()
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        matches_to_remind = []
        for match in matches:
            if match.start_time is None:
                continue
            if not (now <= match.start_time <= self._reminder_window + now):
                continue
            # match start time in [now, now + reminder_window]
            if match.start_time <= self._last_reminded_match_start_time:
                continue  # skipping already processed matches
            matches_to_remind.append(match)

        for match in matches_to_remind:
            self._last_reminded_match_start_time = max(self._last_reminded_match_start_time, match.start_time)
            self._remind_about_match(match, now)

        _logger.info(f'checking reminders finished. {len(matches_to_remind)} new matches processed')

    def _remind_about_match(self, match: matches_data_loader.Dota2Match, now: datetime.datetime):
        match_descriptor = reminders_storage.MatchDescriptor(
            match.team1.liquipedia_page if match.team1 is not None else None,
            match.team2.liquipedia_page if match.team2 is not None else None,
            match.tournament.liquipedia_page)

        reminders = reminders_storage.storage().get_reminded_chat_ids(match_descriptor)

        _logger.info(f'sending {len(reminders)} reminders about match {match_descriptor}')

        for chat_id in reminders:
            self._bot.send_message(
                chat_id=chat_id,
                text='TODO message')
