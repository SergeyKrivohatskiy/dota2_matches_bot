import config

import sys
sys.path.append(config.ROOT_DIR)  # tmp solution. TODO change project structure

import functools
import logging
import typing
import telegram
import telegram.ext
import localization
import reminders_storage
import matches_data_loader
import reminders_sender
import match_printing
import chat_settings
from chat_settings import get_lang


def _inline_keyboard(buttons: typing.List[typing.List[typing.Tuple[str, str]]]):
    return telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton(text, callback_data=data) for text, data in buttons_row]
         for buttons_row in buttons])


_ALL_COMMANDS_NO_UTILITY = ['follow', 'following', 'matches']
_ALL_COMMANDS = ['start', 'help', 'settings', 'stats'] + _ALL_COMMANDS_NO_UTILITY


def _checked_command(command):
    assert(command in _ALL_COMMANDS)
    return command


def admin_only_command():
    def wrapper(command):
        @functools.wraps(command)
        async def wrapped(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id != config.ADMIN_USER_ID:
                logging.warning(f'User {update.effective_user.id}, {update.effective_user.name} tried to access admin'
                                f'command')
                return
            if update.effective_chat.id != config.ADMIN_USER_ID:
                logging.warning(f'User {update.effective_user.name}, in chat {update.effective_chat.id} '
                                f'tried to access admin command')
                return
            return await command(update, context)
        return wrapped
    return wrapper


async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logging.info(f'start called by {update.effective_user.id}')
    for lang in localization.all_locales():
        await context.bot.setMyCommands(
            [(command, localization.get(command + '_cmd_description', lang))
             for command in _ALL_COMMANDS_NO_UTILITY],
            language_code=lang)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=localization.get('start_message', get_lang(update)),
                                   parse_mode='MarkdownV2')


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
        await context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=localization.get('removed_reminder', get_lang(update)))

    return removed


def _generate_command_with_options_keyboard(buttons_per_line: int, command: str, options: typing.Dict[str, str]):
    buttons = []
    buttons_line = []
    for option in sorted(options.keys()):
        buttons_line.append((option, f'{command} {option}'))
        if len(buttons_line) == buttons_per_line:
            buttons.append(buttons_line)
            buttons_line = []

    if len(buttons_line) != 0:
        buttons.append(buttons_line)

    return buttons


async def _process_follow_callbacks(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    rs = reminders_storage.storage()
    followed = False
    if update.callback_query.data == 'follow_all':
        rs.add_all_reminder(str(update.effective_chat.id))
        followed = True
    elif update.callback_query.data == 'follow_team':
        await context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=localization.get('follow_team_select', get_lang(update)),
            reply_markup=_inline_keyboard(_generate_command_with_options_keyboard(
                3, 'follow_team', matches_data_loader.get_teams())))
        return True
    elif update.callback_query.data == 'follow_tournament':
        await context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=localization.get('follow_tournament_select', get_lang(update)),
            reply_markup=_inline_keyboard(_generate_command_with_options_keyboard(
                1, 'follow_tournament', matches_data_loader.get_tournaments())))
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
        await context.bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=localization.get('added_reminder', get_lang(update)))

    return followed


async def _send_settings_begin(update, context, message=None):
    lang = get_lang(update)
    text = localization.get('settings_begin_message', lang)
    markup = _inline_keyboard([[
        (localization.get('settings_close_button', lang), 'settings close'),
        (localization.get('settings_language_button', lang), 'settings to_language')]])
    if message is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=markup)
    else:
        await message.edit_text(text=text, reply_markup=markup)


async def _process_settings_callbacks(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == 'settings to_begin':
        await _send_settings_begin(update, context, update.callback_query.message)
        await context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
        return True
    if update.callback_query.data == 'settings close':
        await update.callback_query.message.delete()
        await context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
        return True
    if update.callback_query.data == 'settings to_language':
        markup = _generate_command_with_options_keyboard(
            5, 'settings change_language', {locale: locale for locale in localization.all_locales()})
        markup.append([(localization.get('settings_back_button', get_lang(update)), 'settings to_begin')])
        await update.callback_query.message.edit_text(
            text=localization.get('settings_language_button', get_lang(update)),
            reply_markup=_inline_keyboard(markup))
        await context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
        return True
    if update.callback_query.data.startswith('settings change_language '):
        lang = update.callback_query.data[len('settings change_language '):]
        if lang not in localization.all_locales():
            logging.warning(f'bad lang value {lang} in change_language')
            await context.bot.answer_callback_query(callback_query_id=update.callback_query.id)
            return True

        chat_settings.set_chat_lang(update.effective_chat.id, lang)
        await _send_settings_begin(update, context, update.callback_query.message)
        await context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text=localization.get('settings_language_changed', get_lang(update)))
        return True

    return False


async def callback_query_handle(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    logging.info(f'callback query {update.callback_query.data} from {update.effective_user.name}')

    if await _process_remove_reminders_callbacks(update, context):
        return
    if await _process_follow_callbacks(update, context):
        return
    if await _process_settings_callbacks(update, context):
        return
    if update.callback_query.data.startswith('show_streams '):
        match_id = int(update.callback_query.data[len('show_streams '):])
        match = next((m for m in matches_data_loader.get_matches() if m.id == match_id), None)
        if match is None:
            await context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text=localization.get('match_not_found', get_lang(update)))
            return
        await match_printing.print_match_streams(context.bot, update.effective_chat.id, get_lang(update), match)
        return

    logging.warning(f'unknown callback query {update.callback_query.data}')


async def help_handler(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await start(update, context)  # TODO actual help?


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
    await _send_settings_begin(update, context)


async def matches(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    for match in matches_data_loader.get_matches():
        await match_printing.print_match_message(context.bot, update.effective_chat.id, get_lang(update), match)


@admin_only_command()
async def stats(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    rs_stats = reminders_storage.storage().get_stats()
    top_teams = '\n'.join([f'{idx + 1}) {name_count[1]}\t- {name_count[0]}'
                           for idx, name_count in enumerate(rs_stats.top_followed_teams)])
    top_tournaments = '\n'.join([f'{idx + 1}) {name_count[1]}\t- {name_count[0]}'
                                 for idx, name_count in enumerate(rs_stats.top_followed_tournaments)])
    message = f'Statistics:\n\n' \
              f'Current data version is {matches_data_loader.get_data_version()}\n' \
              f'There are {rs_stats.unique_chats} unique chats, where reminders were set, ' \
              f'with {rs_stats.active_all_reminders} active all reminders, {rs_stats.active_team_reminders} active ' \
              f'team reminders and {rs_stats.active_tournament_reminders} active tournament reminders.\n\n' \
              f'Top followed teams:\n{top_teams}\n\nTop followed tournaments:\n{top_tournaments}'
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message)


def main():
    logging.basicConfig(
        filename=config.LOG_FILE,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        level=logging.INFO
    )

    logging.info('initializing data loader')
    matches_data_loader.initialize()

    logging.info('initializing reminders storage')
    reminders_storage.initialize()

    logging.info('initializing RemindersSender')
    reminders_sender_ = reminders_sender.RemindersSender()
    reminders_sender_.start()

    logging.info('starting bot')
    application = telegram.ext.ApplicationBuilder().token(config.bot_token()).build()

    application.add_handler(telegram.ext.CallbackQueryHandler(callback_query_handle))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('start'), start))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('help'), help_handler))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('following'), following))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('follow'), follow))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('settings'), settings))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('matches'), matches))
    application.add_handler(telegram.ext.CommandHandler(_checked_command('stats'), stats))

    application.run_polling()


if __name__ == '__main__':
    main()
