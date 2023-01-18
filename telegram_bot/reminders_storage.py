import typing
import threading
import logging
from dataclasses import dataclass


_logger = logging.getLogger('reminders_storage')


@dataclass(eq=False)
class MatchDescriptor:
    team1_id: typing.Optional[str]
    team2_id: typing.Optional[str]
    tournament_id: str


@dataclass()
class ChatReminder:
    type_: typing.Literal['team', 'tournament', 'all']
    value: typing.Optional[str]  # None for all reminder, id to rest

    def __hash__(self):
        return hash((self.type_, self.value))


class RemindersStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._chat_reminders: typing.Dict[str, typing.Set[ChatReminder]] = dict()
        self._team_reminders: typing.Dict[str, typing.Set[str]] = dict()
        self._tournament_reminders: typing.Dict[str, typing.Set[str]] = dict()
        self._all_reminders: typing.Set[str] = set()
        _logger.debug('created storage')

    def _check_chat_exists(self, chat_id):
        if chat_id not in self._chat_reminders:
            self._chat_reminders[chat_id] = set()
            _logger.info(f'new user {chat_id}')

    def _check_team_exists(self, team_id):
        if team_id not in self._team_reminders:
            self._team_reminders[team_id] = set()

    def _check_tournament_exists(self, tournament_id):
        if tournament_id not in self._tournament_reminders:
            self._tournament_reminders[tournament_id] = set()

    def add_team_reminder(self, chat_id: str, team_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            team_reminder = ChatReminder('team', team_id)
            if team_reminder in self._chat_reminders[chat_id]:
                return
            self._chat_reminders[chat_id].add(team_reminder)
            self._check_team_exists(team_id)
            self._team_reminders[team_id].add(chat_id)
            _logger.info(f'new team reminder for {chat_id}, team {team_id}')

    def remove_team_reminder(self, chat_id: str, team_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            team_reminder = ChatReminder('team', team_id)
            if team_reminder not in self._chat_reminders[chat_id]:
                return
            self._chat_reminders[chat_id].remove(team_reminder)
            _logger.info(f'removed team reminder for {chat_id}, team {team_id}')
            if team_id in self._team_reminders:
                self._team_reminders[team_id].remove(chat_id)
            
    def add_tournament_reminder(self, chat_id: str, tournament_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            tournament_reminder = ChatReminder('tournament', tournament_id)
            if tournament_reminder in self._chat_reminders[chat_id]:
                return
            self._chat_reminders[chat_id].add(tournament_reminder)
            self._check_tournament_exists(tournament_id)
            self._tournament_reminders[tournament_id].add(chat_id)
            _logger.info(f'new tournament reminder for {chat_id}, tournament {tournament_id}')

    def remove_tournament_reminder(self, chat_id: str, tournament_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            tournament_reminder = ChatReminder('tournament', tournament_id)
            if tournament_reminder not in self._chat_reminders[chat_id]:
                return
            self._chat_reminders[chat_id].remove(tournament_reminder)
            _logger.info(f'removed tournament reminder for {chat_id}, tournament {tournament_id}')
            if tournament_id in self._tournament_reminders:
                self._tournament_reminders[tournament_id].remove(chat_id)

    def add_all_reminder(self, chat_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            all_reminder = ChatReminder('all', None)
            self._chat_reminders[chat_id].add(all_reminder)
            self._all_reminders.add(chat_id)
            _logger.info(f'new all reminder for {chat_id}')

    def remove_all_reminder(self, chat_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            all_reminder = ChatReminder('all', None)
            if all_reminder not in self._chat_reminders[chat_id]:
                return
            self._chat_reminders[chat_id].remove(all_reminder)
            _logger.info(f'removed all reminder for {chat_id}')
            if chat_id in self._all_reminders:
                self._all_reminders.remove(chat_id)

    def remove_all_reminders(self, chat_id: str):
        with self._lock:
            self._check_chat_exists(chat_id)
            for reminder in self._chat_reminders[chat_id]:
                if reminder.type_ == 'all':
                    self._all_reminders.remove(chat_id)
                elif reminder.type_ == 'team':
                    if reminder.value in self._team_reminders:
                        self._team_reminders[reminder.value].remove(chat_id)
                elif reminder.type_ == 'tournament':
                    if reminder.value in self._tournament_reminders:
                        self._tournament_reminders[reminder.value].remove(chat_id)
            self._chat_reminders[chat_id].clear()
            _logger.info(f'removed all reminders for {chat_id}')

    def _get_team_reminded(self, team_id: typing.Optional[str]):
        if team_id is None or team_id not in self._team_reminders:
            return set()
        return self._team_reminders[team_id]

    def _get_tournament_reminded(self, tournament_id: str):
        if tournament_id not in self._tournament_reminders:
            return set()
        return self._tournament_reminders[tournament_id]

    def get_reminded_chat_ids(self, match_descriptor: MatchDescriptor) -> typing.Set[str]:
        with self._lock:
            result = self._get_team_reminded(match_descriptor.team1_id) | \
                     self._get_team_reminded(match_descriptor.team2_id) | \
                     self._get_tournament_reminded(match_descriptor.tournament_id) | \
                     self._all_reminders
            _logger.info(f'found {len(result)} users to remind about match {str(match_descriptor)}')
            return result

    def get_reminders(self, chat_id: str) -> typing.Set[ChatReminder]:
        with self._lock:
            self._check_chat_exists(chat_id)
            _logger.info(f'reporting {len(self._chat_reminders[chat_id])} reminders for user {chat_id}')
            return self._chat_reminders[chat_id].copy()


_def_storage = RemindersStorage()


def storage() -> RemindersStorage:
    return _def_storage
