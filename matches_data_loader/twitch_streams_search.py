import twitch
import time
import typing
import logging
import re
import requests
import langcodes
import matches_data_loader.config as config
from dataclasses import dataclass


_logger = logging.getLogger('twitch_streams_search')


@dataclass(eq=False)
class StreamInfo:
    channel_login: str
    channel_name: str
    thumbnail: str
    title: str
    language: str
    viewers: int


def _argsort_scores(sequence: typing.List[float]) -> typing.List[int]:
    return [i for (_, i) in sorted([(v, i) for (i, v) in enumerate(sequence)], reverse=True)]


def _by_words_substring_score(string, substring):
    if substring in string:
        return 1.0

    substring_words = substring.split()
    string_words = string.split()
    count = 0
    for substring_word in substring_words:
        if substring_word in string_words:
            count += 1

    return count / len(substring_words) * 0.7


def _score_stream_is_a_match_stream(
        stream: twitch.helix.Stream, team1_name: str, team2_name: str, tournament_name: str) -> float:
    if team1_name is None or team2_name is None or tournament_name is None:
        return 0.0

    stream_title = stream.title.lower()
    team1_name = team1_name.lower()
    team2_name = team2_name.lower()
    tournament_name = tournament_name.lower()

    if 'rerun' in stream_title:
        return 0.0

    tournament_score = _by_words_substring_score(stream_title, tournament_name)
    team1_score = _by_words_substring_score(stream_title, team1_name)
    team2_score = _by_words_substring_score(stream_title, team2_name)

    if tournament_score + team1_score + team2_score == 0:
        return 0.0

    score = 0.0

    score += 0.3 * tournament_score + 0.6 * team1_score + 0.6 * team2_score

    if ' vs ' in stream_title:
        score += 0.1

    if ' by ' in stream_title:
        score += 0.04

    if re.search(r"\d\s?[:\-]\s?\d", stream_title):
        score += 0.1

    if re.search(r"bo%d", stream_title):
        score += 0.07

    if stream.language == 'ru':
        score += 0.2
    elif stream.language == 'en':
        score += 0.05

    if stream.viewer_count > 5400:
        score += 0.3
    elif stream.viewer_count > 1000:
        score += 0.1
    elif stream.viewer_count > 100:
        score += 0.05

    return score


class TwitchDota2Api:
    def __init__(self, client_id=config.TWITCH_CLIENT_ID, client_secret=config.TWITCH_CLIENT_SECRET):
        self._helix = twitch.Helix(client_id, client_secret)
        self._dota2_id = self._helix.game(name='Dota 2').id
        self._next_update = None
        self._reload_dota2_streams_if_needed()

    def find_match_streams(self,
                           team1_name: str,
                           team2_name: str,
                           tournament_name: str) -> typing.List[StreamInfo]:
        self._reload_dota2_streams_if_needed()

        scores = [_score_stream_is_a_match_stream(stream, team1_name, team2_name, tournament_name)
                  for stream in self._streams]

        best_stream_idx_by_score = _argsort_scores(scores)

        min_score = 0.5
        max_streams = 6

        result = []
        for stream_idx in best_stream_idx_by_score:
            score = scores[stream_idx]
            stream = self._streams[stream_idx]

            if score < min_score:
                break

            result.append(StreamInfo(
                channel_login=stream.user.login,
                channel_name=stream.user.display_name,
                thumbnail=stream.thumbnail_url,
                title=stream.title,
                language=stream.language,
                viewers=stream.viewer_count))
            if len(result) == max_streams:
                break

        return result

    def _reload_dota2_streams_if_needed(self):
        now = time.time()
        if self._next_update is not None and now < self._next_update:
            return
        self._reload_dota2_streams()
        self._next_update = now + config.TWITCH_STREAMS_UPDATE_TIMEOUT

    def _reload_dota2_streams(self):
        _logger.info('reloading dota2 streams')

        self._streams: typing.List[twitch.helix.Stream] = \
            list(self._helix.streams(game_id=self._dota2_id, first=twitch.helix.Streams.FIRST_API_LIMIT))

        for stream in self._streams:
            if stream.language == 'other':
                stream.language = 'неизвестный язык'
            else:
                stream.language = langcodes.Language.get(stream.language).display_name('ru')

        _logger.info('dota2 %d streams loaded' % len(self._streams))

    @staticmethod
    def get_thumbnail(uri: str):
        uri = uri.replace('{width}x{height}', '%dx%d' % config.TWITCH_THUMBNAIL_WH, 1)
        _logger.info('loading twitch thumbnail from %s' % uri)
        r = requests.get(uri)
        return r.content


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    api = TwitchDota2Api()

    while True:
        team1 = input()
        team2 = input()
        tournament = input()
        res = api.find_match_streams(team1, team2, tournament)
        print(len(res))
        for s in res:
            print(s.title)
