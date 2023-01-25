import typing
import threading
import logging
import peewee
import telegram_bot.config as config
from dataclasses import dataclass


_logger = logging.getLogger('reminders_storage')


_db = peewee.SqliteDatabase(
    config.REMINDERS_STORAGE_FILE,
    pragmas={
        'journal_mode': 'wal',
        'cache_size': -1 * 64000,
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 0})


class _BaseModel(peewee.Model):
    class Meta:
        database = _db


class _Chat(_BaseModel):
    id = peewee.CharField(unique=True, primary_key=True)


class _Reminder(_BaseModel):
    chat = peewee.ForeignKeyField(_Chat, backref='reminders')
    type = peewee.CharField(max_length=10)
    value = peewee.CharField(null=True)


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


@dataclass()
class Stats:
    unique_chats: int
    active_team_reminders: int
    active_tournament_reminders: int
    active_all_reminders: int
    top_followed_teams: typing.List[typing.Tuple[str, int]]  # name to count (top N entries)
    top_followed_tournaments: typing.List[typing.Tuple[str, int]]  # name to count (top N entries)


class RemindersStorage:
    def __init__(self):
        _logger.info('connecting db')
        _db.connect()
        _logger.info('creating tables')
        _db.create_tables([_Chat, _Reminder])

        _logger.info(f'there are {_Chat.select().count()} chats and {_Reminder.select().count()} reminders '
                     f'stored in the db')

        self._lock = threading.Lock()

    @staticmethod
    def _get_or_create_chat(chat_id):
        chat, created = _Chat.get_or_create(id=chat_id)
        if created:
            _logger.info(f'new chat {chat_id}')
        return chat

    def add_team_reminder(self, chat_id: str, team_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            _, created = _Reminder.get_or_create(chat=chat, type='team', value=team_id)
            if created:
                _logger.info(f'new team reminder for {chat_id}, team {team_id}')

    def remove_team_reminder(self, chat_id: str, team_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            q = _Reminder.delete().where(
                (_Reminder.chat == chat) & (_Reminder.type == 'team') & (_Reminder.value == team_id))
            if q.execute() > 0:
                _logger.info(f'removed team reminder for {chat_id}, team {team_id}')
            
    def add_tournament_reminder(self, chat_id: str, tournament_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            _, created = _Reminder.get_or_create(chat=chat, type='tournament', value=tournament_id)
            if created:
                _logger.info(f'new tournament reminder for {chat_id}, tournament {tournament_id}')

    def remove_tournament_reminder(self, chat_id: str, tournament_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            q = _Reminder.delete().where(
                (_Reminder.chat == chat) & (_Reminder.type == 'tournament') & (_Reminder.value == tournament_id))
            if q.execute() > 0:
                _logger.info(f'removed tournament reminder for {chat_id}, tournament {tournament_id}')

    def add_all_reminder(self, chat_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            _, created = _Reminder.get_or_create(chat=chat, type='all', value=None)
            if created:
                _logger.info(f'new all reminder for {chat_id}')

    def remove_all_reminder(self, chat_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            q = _Reminder.delete().where(
                (_Reminder.chat == chat) & (_Reminder.type == 'all') & (_Reminder.value.is_null()))
            if q.execute() > 0:
                _logger.info(f'removed all reminder for {chat_id}')

    def remove_all_reminders(self, chat_id: str):
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            q = _Reminder.delete().where(_Reminder.chat == chat)
            removed = q.execute()
            if removed > 0:
                _logger.info(f'removed all {removed} reminders for {chat_id}')

    @staticmethod
    def _get_team_reminded(team_id: typing.Optional[str]):
        if team_id is None:
            return set()
        reminders = _Reminder.select().where((_Reminder.type == 'team') & (_Reminder.value == team_id))
        return {reminder.chat.id for reminder in reminders}

    @staticmethod
    def _get_tournament_reminded(tournament_id: str):
        reminders = _Reminder.select().where((_Reminder.type == 'tournament') & (_Reminder.value == tournament_id))
        return {reminder.chat.id for reminder in reminders}

    @staticmethod
    def _all_reminded():
        reminders = _Reminder.select().where((_Reminder.type == 'all') & (_Reminder.value.is_null()))
        return {reminder.chat.id for reminder in reminders}

    def get_reminded_chat_ids(self, match_descriptor: MatchDescriptor) -> typing.Set[str]:
        with self._lock:
            # TODO direct or request
            result = self._get_team_reminded(match_descriptor.team1_id) | \
                     self._get_team_reminded(match_descriptor.team2_id) | \
                     self._get_tournament_reminded(match_descriptor.tournament_id) | \
                     self._all_reminded()
            _logger.info(f'found {len(result)} users to remind about match {str(match_descriptor)}')
            return result

    def get_reminders(self, chat_id: str) -> typing.Set[ChatReminder]:
        with self._lock:
            chat = self._get_or_create_chat(chat_id)
            _logger.info(f'reporting {chat.reminders.count()} reminders for chat {chat_id}')

            result = set()
            for reminder in chat.reminders:
                result.add(ChatReminder(type_=reminder.type, value=reminder.value))
            return result

    @staticmethod
    def _get_top(what: typing.Literal['team', 'tournament']):
        q = _Reminder.select(_Reminder.value, peewee.fn.Count(_Reminder.id).alias('count')) \
            .where(_Reminder.type == what) \
            .group_by(_Reminder.value) \
            .order_by(peewee.fn.Count(_Reminder.id).desc())
        result = []
        for r in q:
            result.append((r.value, r.count))
        return result

    def get_stats(self) -> Stats:
        with self._lock:
            return Stats(
                unique_chats=_Chat.select().count(),
                active_all_reminders=_Reminder.select().where(
                    (_Reminder.type == 'all') & (_Reminder.value.is_null())).count(),
                active_team_reminders=_Reminder.select().where(_Reminder.type == 'team').count(),
                active_tournament_reminders=_Reminder.select().where(_Reminder.type == 'tournament').count(),
                top_followed_teams=self._get_top('team'),
                top_followed_tournaments=self._get_top('tournament')
            )


_def_storage: typing.Optional[RemindersStorage] = None


def storage() -> RemindersStorage:
    global _def_storage
    assert(_def_storage is not None)
    return _def_storage


def initialize():
    global _def_storage
    assert(_def_storage is None)
    _def_storage = RemindersStorage()
