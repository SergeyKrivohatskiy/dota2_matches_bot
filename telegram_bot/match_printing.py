import telegram
import matches_data_loader
import localization
import typing
import datetime
import logging
import re
import config


_logger = logging.getLogger('match_printing')


def _escape(s: str):
    # TODO better impl
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        s = s.replace(c, '\\' + c)
    return s


def _get_tier_text(tournament, lang):
    if tournament.tier is None:
        return ''
    try:
        m = re.match(r'Tier (\d+)', tournament.tier)
        if m is None:
            raise ValueError()
        tier = int(m.group(1))
        if not (1 <= tier <= 4):
            raise ValueError()
    except ValueError:
        _logger.warning(f'bad tournament tier: {tournament.tier}')
        return ''
    tier = [localization.get('tier_1_tournament', lang),
            localization.get('tier_2_tournament', lang),
            localization.get('tier_3_tournament', lang),
            localization.get('tier_4_tournament', lang)][tier - 1]

    return ', ' + tier


def _team_name(team: matches_data_loader.Dota2Team, lang: str):
    if team is None:
        return localization.get('tbd_team', lang)
    return f'*{_escape(team.name)}*'


def _score_str(score: typing.Tuple[int, int]):
    if score == (0, 0):
        return '0:0'
    return '||%d:%d||' % score


def _team_vs_team_string(match: matches_data_loader.Dota2Match, lang: str) -> str:
    has_score = match.score is not None
    score_or_vs = _score_str(match.score) if has_score else 'vs'
    return f'{_team_name(match.team1, lang)} {score_or_vs} {_team_name(match.team2, lang)}'


def _match_message(lang: str, match: matches_data_loader.Dota2Match) -> str:

    def start_time_str(start_time: typing.Optional[datetime.datetime]):
        is_live = match.start_time is None
        if is_live:
            return localization.get('match_live', lang)

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if now > start_time:
            minutes_after_start = ((now - start_time).seconds // 60)
            return localization.get('match_live_with_duration', lang, minutes=minutes_after_start)
        else:
            minutes_before_start = (start_time - now).seconds // 60
            if minutes_before_start < 60:
                return _escape(localization.get('match_starts_soon', lang, minutes=minutes_before_start))
            else:
                hours_before_start = minutes_before_start // 60
                minutes_before_start = minutes_before_start % 60
                return _escape(localization.get('match_starts_in', lang,
                                                minutes=minutes_before_start,
                                                hours=hours_before_start))

    start_time = start_time_str(match.start_time)

    tournament_str = _escape(localization.get('tournament_in_match', lang, name=match.tournament.name))
    tournament_str += _get_tier_text(match.tournament, lang)

    format_str = (' \\(%s\\)' % _escape(match.format)) if match.format is not None else ''

    team_vs_team = _team_vs_team_string(match, lang) + format_str
    match_prefix = localization.get('match_prefix', lang) + ' '
    if len(team_vs_team) <= config.LINE_WIDTH < len(team_vs_team) + len(match_prefix):
        match_prefix = ''  # don't use prefix if it makes line longer than LINE_WIDTH

    return f'{match_prefix}{team_vs_team}\n{start_time}\n{tournament_str}'


async def print_match_message(bot: telegram.Bot, chat_id: int, lang: str, match: matches_data_loader.Dota2Match):
    message = _match_message(lang, match)
    if len(match.streams) == 0:
        reply_markup = None
    else:
        reply_markup = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(
            localization.get('show_streams', lang, count=len(match.streams)),
            callback_data=f'{config.CALLBACK_COMMANDS["show_streams"]} {match.id}'
        )]])
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2')


def _get_stream_md_link(stream):
    return f'[twitch\\.tv/{_escape(stream.channel_name)}](https://www.twitch.tv/{_escape(stream.channel_login)})'


def _streams_str(streams, lang: str):
    res = ''
    viewers = localization.get('viewers_count_prefix', lang)
    for stream in sorted(streams, key=lambda x: x.viewers, reverse=True):
        res += f'\n{_get_stream_md_link(stream)}: {_escape(stream.title)} \\({viewers} {stream.viewers}\\)'
    return res


async def print_match_streams(bot: telegram.Bot, chat_id: int, lang: str, match: matches_data_loader.Dota2Match):
    assert(len(match.streams) != 0)
    header = localization.get('match_streams', lang, team_vs_team=_team_vs_team_string(match, lang))
    await bot.send_message(
        chat_id=chat_id,
        text=header + '\n' + _streams_str(match.streams, lang),
        disable_web_page_preview=True,
        parse_mode='MarkdownV2')


def _run_simple_test():
    match = matches_data_loader.Dota2Match(matches_data_loader.Dota2Team('team name 1', None, 'liq_page', 'icon'),
                                           None,
                                           matches_data_loader.TournamentInfo('tournament_name', 'liq_page', 'Tier 1',
                                                                              '12 - 13', 1234, 21, 'EU'),
                                           [],
                                           (1, 0),
                                           'Bo5',
                                           datetime.datetime.now(tz=datetime.timezone.utc) -
                                           datetime.timedelta(seconds=421),
                                           1)

    print(_match_message('ru', match))
    print()
    print(_match_message('en', match))
    print()
    print(_streams_str(match.streams, 'en'))


if __name__ == '__main__':
    _run_simple_test()
