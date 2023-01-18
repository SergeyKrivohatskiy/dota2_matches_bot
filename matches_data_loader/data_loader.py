import datetime
import threading
import time
import logging
import typing
import liquipedia_dota_api
from dataclasses import dataclass
import matches_data_loader.twitch_streams_search as twitch_streams_search
import matches_data_loader.config as config


_logger = logging.getLogger('data_loader')


@dataclass(eq=False)
class Dota2Team:
    name: str
    region: typing.Optional[str]
    liquipedia_page: str
    icon: str


@dataclass(eq=False)
class TournamentInfo:
    name: str
    liquipedia_page: str
    tier: typing.Optional[str]
    date: typing.Optional[str]
    prize_pool_dollars: typing.Optional[int]
    teams_count: typing.Optional[int]
    location: typing.Optional[str]


@dataclass(eq=False)
class Dota2Match:
    team1: typing.Optional[Dota2Team]  # None means team is to be determined
    team2: typing.Optional[Dota2Team]  # None means team is to be determined
    tournament: TournamentInfo
    streams: typing.List[twitch_streams_search.StreamInfo]  # may be not empty for games starting soon or started
    score: typing.Optional[typing.Tuple[int, int]]  # only present for games in progress
    format: typing.Optional[str]  # None means unknown
    start_time: typing.Optional[datetime.datetime]  # None means game is in progress
    id: int


@dataclass(eq=False)
class _Data:
    upcoming_matches: typing.List[Dota2Match]
    team_names_to_id: typing.Dict[str, str]
    tournament_names_to_id: typing.Dict[str, str]


def _match_starts_soon_or_started(match: liquipedia_dota_api.Dota2Match) -> bool:
    if match.start_time is None:
        return True
    time_starts_soon = match.start_time - datetime.timedelta(minutes=config.STREAM_SEARCH_BEFORE_MATCH_MINUTES)
    return time_starts_soon < datetime.datetime.now(tz=match.start_time.tzinfo)


def _get_team_page_to_region(teams):
    team_page_to_region = dict()
    for team_info in teams:
        team_page_to_region[team_info.liquipedia_page] = team_info.region
    return team_page_to_region


def _name_to_id_map(liquipedia_items: typing.Union[typing.List[liquipedia_dota_api.Dota2Team],
                                                   typing.List[liquipedia_dota_api.Dota2Tournament]]):
    result = dict()
    for item in liquipedia_items:
        result[item.name] = item.liquipedia_page
    return result


def _match_same(old: Dota2Match, new: Dota2Match):
    if old.format != new.format:
        return False
    if old.start_time != new.start_time:
        return False
    if old.tournament.liquipedia_page != new.tournament.liquipedia_page:
        return False

    def check_teams(old_team: Dota2Team, new_team: Dota2Team):
        if old_team is not None:
            if new_team is None:
                return False
            if old_team.liquipedia_page != new_team.liquipedia_page:
                return False
            return True

    if not check_teams(old.team1, new.team1):
        return False
    if not check_teams(old.team2, new.team2):
        return False

    if len(old.streams) > 0 and len(new.streams) == 0:
        return False

    return True


def _match_match_ids(data, new_data):
    for m in data.upcoming_matches:
        for new_m in new_data.upcoming_matches:
            if _match_same(m, new_m):
                new_m.id = m.id


class DataLoader:
    def __init__(self, data_update_period=config.DATA_UPDATE_TIMEOUT):
        self._dota2_api = liquipedia_dota_api.Dota2Api(app_name=config.APP_NAME)
        self._twitch_streams_searcher = twitch_streams_search.TwitchDota2Api()
        self._data: _Data = _Data([], {}, {})
        self._match_id = 0
        self._data_version = 0
        self._data_lock = threading.Lock()
        self._data_update_stop_event = threading.Event()
        self._data_update_period = data_update_period
        self._data_update_thread = threading.Thread(target=self._data_update_loop, daemon=True)
        self._data_update_thread.start()

    def __del__(self):
        self.stop_data_update()

    def data(self) -> _Data:
        with self._data_lock:
            return self._data

    def data_version(self):
        with self._data_lock:
            return self._data_version

    def stop_data_update(self):
        if self._data_update_stop_event.is_set():
            return
        _logger.info('Stopping data updating')
        self._data_update_stop_event.set()
        self._data_update_thread.join()

    def _data_update(self):
        try:
            _logger.info('Started data updating')
            matches: typing.List[liquipedia_dota_api.Dota2Match] = self._dota2_api.get_matches()
            matches = matches[:config.MAXIMUM_MATCHES_TO_LOAD]
            streams: typing.List[typing.List[twitch_streams_search.StreamInfo]] = self._get_streams_info(matches)

            # TODO maybe do not update every time
            teams: typing.List[liquipedia_dota_api.Dota2Team] = self._dota2_api.get_teams()
            _logger.info('%d teams loaded' % len(teams))

            # TODO maybe do not update every time
            tournaments = self._dota2_api.get_tournaments()
            _logger.info('%d tournaments loaded' % len(tournaments))

            team_page_to_region = _get_team_page_to_region(teams)

            def region_info(source: liquipedia_dota_api.Dota2TeamInMatch):
                if source.liquipedia_page in team_page_to_region:
                    return team_page_to_region[source.liquipedia_page]
                else:
                    _logger.info('team %s region not found' % source.name)
                    return None

            def get_team_info(source: liquipedia_dota_api.Dota2TeamInMatch):
                if source is None:
                    return None
                return Dota2Team(source.name, region_info(source), source.liquipedia_page, source.icon)

            tournament_page_tournament = dict()
            for tournaments_info in tournaments:
                tournament_page_tournament[tournaments_info.liquipedia_page] = tournaments_info

            def get_tournament_info(source: liquipedia_dota_api.TournamentInfoInMatch):
                if source.liquipedia_page in tournament_page_tournament:
                    info = tournament_page_tournament[source.liquipedia_page]
                    location = info.location
                    prize_pool_dollars = info.prize_pool_dollars
                    tier = info.tier
                    date = info.date
                    teams_count = info.teams_count
                else:
                    _logger.info('tournament %s info not found' % source.name)
                    location = None
                    prize_pool_dollars = None
                    tier = None
                    date = None
                    teams_count = None

                return TournamentInfo(source.name, source.liquipedia_page,
                                      tier, date, prize_pool_dollars, teams_count, location)

            new_matches: typing.List[Dota2Match] = []
            for match, streams_info in zip(matches, streams):
                new_matches.append(Dota2Match(
                    get_team_info(match.team1), get_team_info(match.team2),
                    get_tournament_info(match.tournament),
                    streams_info,
                    match.score,
                    match.format,
                    match.start_time,
                    self._match_id))
                self._match_id += 1

            self._update_data(_Data(new_matches, _name_to_id_map(teams), _name_to_id_map(tournaments)))
        except liquipedia_dota_api.RequestsException as e:
            _logger.error('Dota2Api RequestsException. Code: %d' % e.code, exc_info=e)
            if self._data is not None:
                return
        except Exception as e:
            _logger.error('Dota2Api Exception', exc_info=e)

    def _data_update_loop(self):
        while True:
            self._data_update()
            if self._data_update_stop_event.wait(self._data_update_period):
                break

    def _get_streams_info(self, matches):
        streams = []
        for match in matches:
            streams.append(self._search_streams(match))
        return streams

    def _search_streams(self, match) -> typing.List[twitch_streams_search.StreamInfo]:
        if not _match_starts_soon_or_started(match) or match.team1 is None or match.team2 is None:
            return []

        return self._twitch_streams_searcher.find_match_streams(
            match.team1.name, match.team2.name, match.tournament.name)

    def _update_data(self, new_data: _Data):
        with self._data_lock:
            _match_match_ids(self._data, new_data)
            self._data = new_data
            self._data_version += 1
            _logger.info('Data updating finished. %d matches saved, %d teams and %d tournaments. Version %d' %
                         (len(self._data.upcoming_matches),
                          len(self._data.team_names_to_id),
                          len(self._data.tournament_names_to_id),
                          self._data_version))


def _run_data_loader():
    logging.basicConfig(level=logging.INFO)
    data_provider = DataLoader(data_update_period=config.DATA_UPDATE_TIMEOUT)
    try:
        while True:
            _logger.info('Data loader is running. Data version %d' % data_provider.data_version())
            time.sleep(config.DATA_UPDATE_TIMEOUT * 2)
    except KeyboardInterrupt:
        data_provider.stop_data_update()


if __name__ == '__main__':
    _run_data_loader()
