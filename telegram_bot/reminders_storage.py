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
class UserReminder:
    type_: typing.Literal['team', 'tournament', 'all']
    value: typing.Optional[str]  # None for all reminder, id to rest

    def __hash__(self):
        return hash((self.type_, self.value))


class RemindersStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._user_reminders: typing.Dict[str, typing.Set[UserReminder]] = dict()
        self._team_reminders: typing.Dict[str, typing.Set[str]] = dict()
        self._tournament_reminders: typing.Dict[str, typing.Set[str]] = dict()
        self._all_reminders: typing.Set[str] = set()
        _logger.debug('created storage')

    def _check_user_exists(self, user_id):
        if user_id not in self._user_reminders:
            self._user_reminders[user_id] = set()
            _logger.info(f'new user {user_id}')

    def _check_team_exists(self, team_id):
        if team_id not in self._team_reminders:
            self._team_reminders[team_id] = set()

    def _check_tournament_exists(self, tournament_id):
        if tournament_id not in self._tournament_reminders:
            self._tournament_reminders[tournament_id] = set()

    def add_team_reminder(self, user_id: str, team_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            team_reminder = UserReminder('team', team_id)
            if team_reminder in self._user_reminders[user_id]:
                return
            self._user_reminders[user_id].add(team_reminder)
            self._check_team_exists(team_id)
            self._team_reminders[team_id].add(user_id)
            _logger.info(f'new team reminder for {user_id}, team {team_id}')

    def remove_team_reminder(self, user_id: str, team_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            team_reminder = UserReminder('team', team_id)
            if team_reminder not in self._user_reminders[user_id]:
                return
            self._user_reminders[user_id].remove(team_reminder)
            _logger.info(f'removed team reminder for {user_id}, team {team_id}')
            if team_id in self._team_reminders:
                self._team_reminders[team_id].remove(user_id)
            
    def add_tournament_reminder(self, user_id: str, tournament_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            tournament_reminder = UserReminder('tournament', tournament_id)
            if tournament_reminder in self._user_reminders[user_id]:
                return
            self._user_reminders[user_id].add(tournament_reminder)
            self._check_tournament_exists(tournament_id)
            self._tournament_reminders[tournament_id].add(user_id)
            _logger.info(f'new tournament reminder for {user_id}, tournament {tournament_id}')

    def remove_tournament_reminder(self, user_id: str, tournament_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            tournament_reminder = UserReminder('tournament', tournament_id)
            if tournament_reminder not in self._user_reminders[user_id]:
                return
            self._user_reminders[user_id].remove(tournament_reminder)
            _logger.info(f'removed tournament reminder for {user_id}, tournament {tournament_id}')
            if tournament_id in self._tournament_reminders:
                self._tournament_reminders[tournament_id].remove(user_id)

    def add_all_reminder(self, user_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            all_reminder = UserReminder('all', None)
            self._user_reminders[user_id].add(all_reminder)
            self._all_reminders.add(user_id)
            _logger.info(f'new all reminder for {user_id}')

    def remove_all_reminder(self, user_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            all_reminder = UserReminder('all', None)
            if all_reminder not in self._user_reminders[user_id]:
                return
            self._user_reminders[user_id].remove(all_reminder)
            _logger.info(f'removed all reminder for {user_id}')
            if user_id in self._all_reminders:
                self._all_reminders.remove(user_id)

    def remove_all_reminders(self, user_id: str):
        with self._lock:
            self._check_user_exists(user_id)
            for reminder in self._user_reminders[user_id]:
                if reminder.type_ == 'all':
                    self._all_reminders.remove(user_id)
                elif reminder.type_ == 'team':
                    if reminder.value in self._team_reminders:
                        self._team_reminders[reminder.value].remove(user_id)
                elif reminder.type_ == 'tournament':
                    if reminder.value in self._tournament_reminders:
                        self._tournament_reminders[reminder.value].remove(user_id)
            self._user_reminders[user_id].clear()
            _logger.info(f'removed all reminders for {user_id}')

    def _get_team_reminded(self, team_id: typing.Optional[str]):
        if team_id is None or team_id not in self._team_reminders:
            return set()
        return self._team_reminders[team_id]

    def _get_tournament_reminded(self, tournament_id: str):
        if tournament_id not in self._tournament_reminders:
            return set()
        return self._tournament_reminders[tournament_id]

    def get_reminded_user_ids(self, match_descriptor: MatchDescriptor) -> typing.Set[str]:
        with self._lock:
            result = self._get_team_reminded(match_descriptor.team1_id) | \
                     self._get_team_reminded(match_descriptor.team2_id) | \
                     self._get_tournament_reminded(match_descriptor.tournament_id) | \
                     self._all_reminders
            _logger.info(f'found {len(result)} users to remind about match {str(match_descriptor)}')
            return result

    def get_reminders(self, user_id: str) -> typing.Set[UserReminder]:
        with self._lock:
            self._check_user_exists(user_id)
            _logger.info(f'reporting {len(self._user_reminders[user_id])} reminders for user {user_id}')
            return self._user_reminders[user_id]


_def_storage = RemindersStorage()


def storage() -> RemindersStorage:
    return _def_storage
