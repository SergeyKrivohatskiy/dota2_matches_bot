import datetime
import logging

from liquipedia_dota_api.dota2_api_base import Dota2ApiBase
from liquipedia_dota_api.config import DEFAULT_PARSE_PERIOD, DEFAULT_GET_PERIOD
from liquipedia_dota_api.dota2_dataclasses import *

__all__ = ['Dota2Api', 'DEFAULT_PARSE_PERIOD', 'DEFAULT_GET_PERIOD',
           'Dota2Team', 'Dota2Match', 'Dota2Tournament', 'Dota2TeamInMatch', 'TournamentInfoInMatch']


def _parse_team_in_match(team_info):
    maybe_team_name = team_info.span.get('data-highlightingclass')
    if maybe_team_name == 'TBD':
        return None
    return Dota2TeamInMatch(name=maybe_team_name,
                            liquipedia_page=team_info.a.get('href'),
                            icon=team_info.img.get('src'))


def _parse_score(score_and_format):
    if score_and_format.div is None:
        return None
    score_text = score_and_format.div.text
    if 'vs' in score_text:
        return None
    assert ':' in score_text
    result = tuple([int(wins) for wins in score_text.split(':')])
    assert len(result) == 2
    return result


def _parse_tournament(tournament_info):
    return TournamentInfoInMatch(name=tournament_info.a.get('title'),
                                 liquipedia_page=tournament_info.a.get('href'),
                                 icon=tournament_info.img.get('src'))


def _parse_match_format(score_and_format):
    if score_and_format.abbr is None:
        return None
    return score_and_format.abbr.text


def _parse_match(match_table):
    vs_row, info_row = match_table('tr')
    team1_info, score_and_format, team2_info = vs_row('td')
    countdown = info_row.td.span
    tournament_info = info_row.td.div

    team1 = _parse_team_in_match(team1_info)
    team2 = _parse_team_in_match(team2_info)

    match_format = _parse_match_format(score_and_format)
    score = _parse_score(score_and_format)

    match_start_timestamp = int(countdown.span.get('data-timestamp'))
    match_start_time = datetime.datetime.fromtimestamp(match_start_timestamp, tz=datetime.timezone.utc)

    tournament = _parse_tournament(tournament_info)

    return Dota2Match(team1, team2, tournament, score, match_format, match_start_time)


class Dota2Api:
    def __init__(self, app_name: str,
                 parse_period: float = DEFAULT_PARSE_PERIOD, get_period: float = DEFAULT_GET_PERIOD):
        """
        A class for parsing data from dota2 liquipedia pages

        :param app_name: "User-Agent" that identifies your project / use of the API, and includes contact
                         information. Example: "LiveScoresBot/1.0 (http://www.example.com/; email@example.com)".
                         Generic user agents such as "Python-requests", "Go-http-client", etc are more likely to be
                         blocked. See https://liquipedia.net/api-terms-of-use for details
        :param parse_period: a rate limit for parse method will be one request per parse_period
        :param get_period: a rate limit for get method will be one request per get_period
        """
        self._base = Dota2ApiBase(app_name, parse_period, get_period)

    def get_teams(self) -> typing.List[Dota2Team]:
        soup, _ = self._base.parse('Portal:Teams')
        notable_teams = soup('div', 'lp-container-fluid')[0]
        region_panels = notable_teams('div', 'panel-box')

        teams = list()

        for region_panel in region_panels:
            region_name = region_panel.find('div', 'panel-box-heading').text

            team_rows = region_panel.find('div', 'panel-box-body')
            for team_row in team_rows.contents:
                if team_row.img is None:
                    continue  # a possible error on liquipedia page
                icon_link = team_row.img.get('src')

                team_a = team_row.find('span', 'team-template-text').contents[0]
                team_name = team_a.text
                team_page_link = team_a.get('href')

                team_name = team_name[:60]  # TODO better fix for callback len
                teams.append(Dota2Team(team_name, region_name, team_page_link, icon_link))

        return teams

    def get_tournaments(self) -> typing.List[Dota2Tournament]:
        soup, _ = self._base.parse('Portal:Tournaments')
        ongoing_tournaments_table = soup('div', 'table-responsive')[1]
        tournament_rows = ongoing_tournaments_table('div', 'divRow')

        result = list()

        for tournament_row in tournament_rows:
            cells = tournament_row('div', 'divCell')

            tier = cells[0].a.text
            liquipedia_page = cells[1].b.a.get('href')
            name = cells[1].b.a.text
            date = cells[2].text
            prize_str: str = cells[3].text
            prize = None
            if prize_str.startswith('$'):
                prize_str = prize_str[1:].replace(',', '')
                if prize_str.isdigit():
                    prize = int(prize_str)
            teams = cells[4].text.replace('\xa0teams', '')
            teams = int(teams) if teams.isdigit() else None
            location = cells[5].text.replace('\xa0', ' ').strip()

            name = name[:60]  # TODO better fix for callback len
            result.append(Dota2Tournament(name, liquipedia_page, tier, date, prize, teams, location))

        return result

    def get_matches(self, featured=False) -> typing.List[Dota2Match]:
        list_type = 2 if featured else 1

        soup, _ = self._base.parse('Liquipedia:Upcoming_and_ongoing_matches')
        matches_soup = soup.select('div[data-toggle-area-content="%d"]' % list_type)[0]
        match_tables = matches_soup('table')

        matches = list()

        for match_table in match_tables:
            try:
                match = _parse_match(match_table)
                matches.append(match)
            except Exception as e:
                logging.error('failed to parse match\n' + match_table.prettify(), exc_info=e)

        return matches

    def get_icon(self, icon_path: str) -> bytes:
        return self._base.get(icon_path)
