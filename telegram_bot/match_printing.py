import telegram
import matches_data_loader
import localization
import typing
import datetime
import logging
import re
from dataclasses import dataclass


_logger = logging.getLogger('match_printing')


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
        res += f'\n{_get_stream_md_link(stream)}: {_escape(stream.title)} \\({stream.viewers}\\)'
    return res


def _get_tier_icon(tournament, lang):
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


@dataclass(eq=False)
class MatchMessage:
    message: str  # Markdown message
    streams_message: str  # Markdown message


def match_message(lang: str, match: matches_data_loader.Dota2Match) -> str:
    def team_name(team: matches_data_loader.Dota2Team):
        if team is None:
            return localization.get('tbd_team', lang)
        return f'*{_escape(team.name)}*'

    def score_str(score: typing.Tuple[int, int]):
        return '||%d:%d||' % score

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
    has_score = match.score is not None
    score_or_vs = score_str(match.score) if has_score else 'vs'
    format_str = (' \\(%s\\)' % _escape(match.format)) if match.format is not None else ''

    tournament_str = _escape(localization.get('tournament_in_match', lang, name=match.tournament.name))
    tournament_str += _get_tier_icon(match.tournament, lang)

    return f'{team_name(match.team1)} {score_or_vs} {team_name(match.team2)}{format_str}\n{start_time}\n' \
           f'{tournament_str}'


async def print_match_message(bot: telegram.Bot, chat_id: int, lang: str, match: matches_data_loader.Dota2Match):
    message = match_message(lang, match)
    if len(match.streams) == 0:
        reply_markup = None
    else:
        reply_markup = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(
            localization.get('show_streams', lang, count=len(match.streams)),
            callback_data=f'show_streams {match.id}'
        )]])
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2')


async def print_match_streams(bot: telegram.Bot, chat_id: int, lang: str, match: matches_data_loader.Dota2Match):
    assert(len(match.streams) != 0)
    await bot.send_message(
        chat_id=chat_id,
        text=_streams_str(match.streams),
        disable_web_page_preview=True,
        parse_mode='MarkdownV2')


def _run_simple_test():
    match = matches_data_loader.Dota2Match(matches_data_loader.Dota2Team('team name 1', None, 'liq_page', 'icon'),
                                           None,
                                           matches_data_loader.TournamentInfo('tournament_name', 'liq_page', 1,
                                                                              '12 - 13', 1234, 21, 'EU'),
                                           [],
                                           (1, 0),
                                           'Bo5',
                                           datetime.datetime.now(tz=datetime.timezone.utc) -
                                           datetime.timedelta(seconds=421))

    print(match_message('ru', match))
    print()
    print(match_message('en', match))


if __name__ == '__main__':
    _run_simple_test()
