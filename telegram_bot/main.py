import logging
import telegram
import telegram.ext
import config
import matches_data_loader


async def start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logging.info(f'start called by {update.effective_user.name}!')
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f'Hello {update.effective_user.name}! The bot is under development..')


async def matches(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    for match in matches_data_loader.get_matches():
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Match {match.team1.name if match.team1 is not None else "TBD"} vs '
                 f'{match.team2.name if match.team2 is not None else "TBD"}')


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logging.info('starting bot')
    application = telegram.ext.ApplicationBuilder().token(config.BOT_TOKEN).build()

    application.add_handler(telegram.ext.CommandHandler('start', start))
    application.add_handler(telegram.ext.CommandHandler('matches', matches))

    application.run_polling()


if __name__ == '__main__':
    main()
