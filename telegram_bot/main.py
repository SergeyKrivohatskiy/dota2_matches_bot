import datetime
import logging
import typing
import telegram
import telegram.ext
import config
import localization
import reminders_storage
import matches_data_loader
import reminders_sender
from chat_settings import get_lang


def _inline_keyboard(buttons: typing.List[typing.List[typing.Tuple[str, str]]]):
    return telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton(text, callback_data=data) for text, data in buttons_row]
         for buttons_row in buttons])


async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logging.info(f'start called by {update.effective_user.name}')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=localization.get('start_message', get_lang(update)),
                                   parse_mode='MarkdownV2',
                                   reply_markup=_inline_keyboard([[('text1', 'data1'), ('text2', 'data2')],
                                                                  [('text3', 'data3')]]))


async def _process_remove_reminders_callbacks(
        update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> bool:
    rs = reminders_storage.storage()
    removed = False
    if update.callback_query.data == 'remove_all_reminders':
        rs.remove_all_reminders(str(update.effective_chat.id))
        removed = True
    elif update.callback_query.data == 'remove_all_reminder':
        rs.remove_all_reminder(str(update.effective_chat.id))
        removed = True
    elif update.callback_query.data.startswith('remove_tournament_reminder '):
        tournament = update.callback_query.data[len('remove_tournament_reminder '):]
        rs.remove_tournament_reminder(str(update.effective_chat.id), tournament)
        removed = True
    elif update.callback_query.data.startswith('remove_team_reminder '):
        team = update.callback_query.data[len('remove_team_reminder '):]
        rs.remove_team_reminder(str(update.effective_chat.id), team)
        removed = True

    if removed:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=localization.get('removed_reminder', get_lang(update)))

    return removed


def _generate_command_with_options_keyboard(buttons_per_line: int, command: str, options: typing.Dict[str, str]):
    buttons = []
    buttons_line = []
    for option in options.keys():
        buttons_line.append((option, f'{command} {option}'))
        if len(buttons_line) == buttons_per_line:
            buttons.append(buttons_line)
            buttons_line = []

    if len(buttons_line) != 0:
        buttons.append(buttons_line)

    return _inline_keyboard(buttons)


async def _process_follow_callbacks(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    rs = reminders_storage.storage()
    followed = False
    if update.callback_query.data == 'follow_all':
        rs.add_all_reminder(str(update.effective_chat.id))
        followed = True
    elif update.callback_query.data == 'follow_team':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=localization.get('follow_team_select', get_lang(update)),
            reply_markup=_generate_command_with_options_keyboard(
                3, 'follow_team', matches_data_loader.get_teams()))
        return True
    elif update.callback_query.data == 'follow_tournament':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=localization.get('follow_tournament_select', get_lang(update)),
            reply_markup=_generate_command_with_options_keyboard(
                1, 'follow_tournament', matches_data_loader.get_tournaments()))
        return True
    elif update.callback_query.data.startswith('follow_tournament '):
        tournament = update.callback_query.data[len('follow_tournament '):]
        # TODO check validity?
        rs.add_tournament_reminder(str(update.effective_chat.id), tournament)
        followed = True
    elif update.callback_query.data.startswith('follow_team '):
        team = update.callback_query.data[len('follow_team '):]
        # TODO check validity?
        rs.add_team_reminder(str(update.effective_chat.id), team)
        followed = True

    if followed:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=localization.get('added_reminder', get_lang(update)))

    return followed


async def callback_query_handle(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f'callback query {update.callback_query.data} from {update.effective_user.name}')

    if await _process_remove_reminders_callbacks(update, context):
        return
    if await _process_follow_callbacks(update, context):
        return

    logging.warning(f'unknown callback query {update.callback_query.data}')


async def help_handler(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='TODO')


async def following(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    rs = reminders_storage.storage()
    reminders = rs.get_reminders(str(update.effective_chat.id))
    if len(reminders) != 0:
        reply_markup = _inline_keyboard(
            [[(localization.get('remove_all_reminders', get_lang(update)), 'remove_all_reminders')]])
    else:
        reply_markup = None
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=localization.get('reminders_count', get_lang(update), count=len(reminders)),
        reply_markup=reply_markup)

    for reminder in reminders:
        if reminder.type_ == 'team':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=localization.get('following_team', get_lang(update),
                                      team=reminder.value),
                reply_markup=_inline_keyboard(
                    [[(localization.get('remove_reminder', get_lang(update)),
                       'remove_team_reminder ' + reminder.value)]]))
        elif reminder.type_ == 'tournament':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=localization.get('following_tournament', get_lang(update),
                                      tournament=reminder.value),
                reply_markup=_inline_keyboard(
                    [[(localization.get('remove_reminder', get_lang(update)),
                       'remove_tournament_reminder ' + reminder.value)]]))
        elif reminder.type_ == 'all':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=localization.get('following_all', get_lang(update)),
                reply_markup=_inline_keyboard(
                    [[(localization.get('remove_reminder', get_lang(update)),
                       'remove_all_reminder')]]))


async def follow(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=localization.get('follow_message', get_lang(update)),
        reply_markup=_inline_keyboard(
            [[(localization.get('follow_all', get_lang(update)), 'follow_all'),
              (localization.get('follow_team', get_lang(update)), 'follow_team'),
              (localization.get('follow_tournament', get_lang(update)), 'follow_tournament')]]))


async def settings(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='TODO')


def _escape(s: str):
    # TODO better impl
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        s = s.replace(c, '\\' + c)
    return s


def _streams_str(streams):
    res = ''
    for stream in sorted(streams, key=lambda x: x.viewers, reverse=True):
        res += f'\n[{_escape(stream.channel_name)}](https://www.twitch.tv/{stream.channel_login}): {_escape(stream.title)} ' \
               f'\\({stream.viewers}\\)'
    return res


def _match_message(update: telegram.Update, match: matches_data_loader.Dota2Match):
    lang = get_lang(update)

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

    logging.info('initializing RemindersSender')
    reminders_sender_ = reminders_sender.RemindersSender()
    reminders_sender_.start()

    logging.info('starting bot')
    application = telegram.ext.ApplicationBuilder().token(config.BOT_TOKEN).build()

    application.add_handler(telegram.ext.CallbackQueryHandler(callback_query_handle))
    application.add_handler(telegram.ext.CommandHandler('start', start))
    application.add_handler(telegram.ext.CommandHandler('help', help_handler))
    application.add_handler(telegram.ext.CommandHandler('following', following))
    application.add_handler(telegram.ext.CommandHandler('follow', follow))
    application.add_handler(telegram.ext.CommandHandler('settings', settings))
    application.add_handler(telegram.ext.CommandHandler('matches', matches))

    application.run_polling()


if __name__ == '__main__':
    main()
