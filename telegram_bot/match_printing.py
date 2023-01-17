import matches_data_loader
import localization
import typing
import datetime


def _escape(s: str):
    # TODO better impl
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        s = s.replace(c, '\\' + c)
    return s


def _get_stream_md_link(stream):
    return f'[{_escape(stream.channel_name)}](https://www.twitch.tv/{_escape(stream.channel_login)})'


def _streams_str(streams):
    res = ''
    for stream in sorted(streams, key=lambda x: x.viewers, reverse=True):
        res += f'\n{_get_stream_md_link(stream)}): {_escape(stream.title)} \\({stream.viewers}\\)'
    return res


def match_message(lang: str, match: matches_data_loader.Dota2Match):
    def team_name(team: matches_data_loader.Dota2Team):
        if team is None:
            return localization.get('tbd_team', lang)
        return f'*{_escape(team.name)}*'

    def score_str(score: typing.Tuple[int, int]):
        return '||%d:%d||' % score

    def start_time_str(start_time: typing.Optional[datetime.datetime]):
        # TODO
        is_live = match.start_time is None
        if is_live:
            return 'live'
        return _escape('TODO time')

    start_time = start_time_str(match.start_time)
    has_score = match.score is not None
    score_or_vs = score_str(match.score) if has_score else 'vs'
    format_str = (' \\(%s\\)' % _escape(match.format)) if match.format is not None else ''

    tournament_str = _escape(match.tournament.name)

    streams_str = ''  # TODO _streams_str(match.streams)

    return f'{team_name(match.team1)} {score_or_vs} {team_name(match.team2)}{format_str} {start_time}\n'\
           f'{tournament_str}'\
           f'{streams_str}'
