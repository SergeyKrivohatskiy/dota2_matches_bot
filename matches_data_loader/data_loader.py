import datetime
import threading
import time
import logging
import typing
import liquipedia_dota_api
import matches_data_loader.twitch_streams_search as twitch_streams_search
import matches_data_loader.config as config


def _match_starts_soon_or_started(match: liquipedia_dota_api.Dota2Match) -> bool:
    if match.start_time is None:
        return True
    time_starts_soon = match.start_time - datetime.timedelta(minutes=config.STREAM_SEARCH_BEFORE_MATCH_MINUTES)
    return time_starts_soon < datetime.datetime.now(tz=match.start_time.tzinfo)


class DataLoader:
    def __init__(self, data_update_period=config.DATA_UPDATE_TIMEOUT):
        self._dota2_api = liquipedia_dota_api.Dota2Api(app_name=config.APP_NAME)
        self._twitch_streams_searcher = twitch_streams_search.TwitchDota2Api()
        self._data = []
        self._data_version = 0
        self._data_lock = threading.Lock()
        self._data_update_stop_event = threading.Event()
        self._data_update_period = data_update_period
        self._data_update_thread = threading.Thread(target=self._data_update_loop, daemon=True)
        self._data_update_thread.start()

    def __del__(self):
        self.stop_data_update()

    def data(self):
        with self._data_lock:
            return self._data

    def data_version(self):
        with self._data_lock:
            return self._data_version

    def stop_data_update(self):
        if self._data_update_stop_event.is_set():
            return
        logging.info('Stopping data updating')
        self._data_update_stop_event.set()
        self._data_update_thread.join()

    def _data_update(self):
        try:
            logging.info('Started data updating')
            matches = self._dota2_api.get_matches()
            matches = self._add_streams_info(matches)

            teams = self._dota2_api.get_teams()  # TODO maybe do not update every time
            logging.info('%d teams loaded' % len(teams))
            matches = self._add_team_regions_info(matches, teams)

            tournaments = self._dota2_api.get_tournaments()  # TODO maybe do not update every time
            logging.info('%d tournaments loaded' % len(tournaments))
            matches = self._add_tournaments_info(matches, tournaments)

            saved_matches = matches[:config.MAXIMUM_MATCHES_TO_SHOW]

            with self._data_lock:
                self._data = saved_matches
                self._data_version += 1
            logging.info('Data updating finished. %d matches loaded. %d matches saved. Version %d' %
                         (len(matches), len(saved_matches), self.data_version()))
        except liquipedia_dota_api.RequestsException as e:
            logging.error('Dota2Api RequestsException. Code: %d' % e.code, exc_info=e)
            if self._data is not None:
                return
        except Exception as e:
            logging.error('Dota2Api Exception', exc_info=e)

    def _data_update_loop(self):
        while True:
            self._data_update()
            if self._data_update_stop_event.wait(self._data_update_period):
                break

    def _add_streams_info(self, matches):
        for match in matches:
            match.streams = self._search_streams(match)
        return matches

    def _search_streams(self, match) -> typing.List[twitch_streams_search.StreamInfo]:
        if not _match_starts_soon_or_started(match) or match.team1 is None or match.team2 is None:
            return []

        return self._twitch_streams_searcher.find_match_streams(
            match.team1.name, match.team2.name, match.tournament.name)

    @staticmethod
    def _add_team_regions_info(matches, teams: typing.List[liquipedia_dota_api.Dota2Team]):
        team_page_to_region = dict()
        for team_info in teams:
            team_page_to_region[team_info.liquipedia_page] = team_info.region

        def add_region_info(team):
            if team is None:
                return
            if team.liquipedia_page in team_page_to_region:
                team.region = team_page_to_region[team.liquipedia_page]
            else:
                logging.info('team %s region not found' % team.name)
                team.region = None

        for match in matches:
            add_region_info(match.team1)
            add_region_info(match.team2)

        return matches

    @staticmethod
    def _add_tournaments_info(matches, tournaments):
        tournament_page_tournament = dict()
        for tournaments_info in tournaments:
            tournament_page_tournament[tournaments_info.liquipedia_page] = tournaments_info

        for match in matches:
            tournament = match.tournament
            if tournament.liquipedia_page not in tournament_page_tournament:
                logging.info('tournament %s info not found' % tournament.name)
                tournament.location = None
                tournament.prize_pool_dollars = None
                tournament.tier = None
                tournament.date = None
                tournament.teams_count = None
                continue

            tournaments_info = tournament_page_tournament[tournament.liquipedia_page]

            tournament.location = tournaments_info.location
            tournament.prize_pool_dollars = tournaments_info.prize_pool_dollars
            tournament.tier = tournaments_info.tier
            tournament.date = tournaments_info.date
            tournament.teams_count = tournaments_info.teams_count

        return matches


def _run_data_loader():
    logging.basicConfig(level=logging.INFO)
    data_provider = DataLoader(data_update_period=config.DATA_UPDATE_TIMEOUT)
    try:
        while True:
            logging.info('Data loader is running. Data version %d' % data_provider.data_version())
            time.sleep(config.DATA_UPDATE_TIMEOUT * 2)
    except KeyboardInterrupt:
        data_provider.stop_data_update()


if __name__ == '__main__':
    _run_data_loader()
