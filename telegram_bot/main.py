import datetime
import logging
import typing
import telegram
import telegram.ext
import config
import localization
import matches_data_loader


async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logging.info(f'start called by {update.effective_user.name}!')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=localization.get('start_message', update.effective_user.language_code),
                                   parse_mode='MarkdownV2',
                                   reply_markup=telegram.ReplyKeyboardMarkup([['11', '/start'], ['/matches', '22']]))


async def help_handler(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='TODO')


async def settings(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='TODO')


def _escape(s: str):
    # TODO better impl
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        s = s.replace(c, '\\' + c)
    return s


def _streams_str(streams):
    if len(streams) == 0:
        return ''
    res = '\n'
    for stream in streams:
        res += f'[{stream.channel_name}](https://www.twitch.tv/{stream.channel_login}): {_escape(stream.title)} ' \
               f'\\({stream.viewers}\\)'
    return res


def _match_message(update: telegram.Update, match: matches_data_loader.Dota2Match):
    lang = update.effective_user.language_code

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

    streams_str = _streams_str(match.streams)

    return f'{team_name(match.team1)} {score_or_vs} {team_name(match.team2)}{format_str} {start_time}\n'\
           f'{tournament_str}'\
           f'{streams_str}'


async def matches(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    for match in matches_data_loader.get_matches():
        await context.bot.send_message(chat_id=update.effective_chat.id, text=_match_message(update, match),
                                       parse_mode='MarkdownV2')


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logging.info('initializing data loader')
    matches_data_loader.initialize()

    logging.info('starting bot')
    application = telegram.ext.ApplicationBuilder().token(config.BOT_TOKEN).build()

    application.add_handler(telegram.ext.CommandHandler('start', start))
    application.add_handler(telegram.ext.CommandHandler('help', help_handler))
    application.add_handler(telegram.ext.CommandHandler('settings', settings))
    application.add_handler(telegram.ext.CommandHandler('matches', matches))

    application.run_polling()


if __name__ == '__main__':
    main()
