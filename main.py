import os
import sys

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, ConversationHandler,
                          Updater)

from storage_choosing import get_choosing_handler
from telegram_handlers import get_handler_person
from load import logger, mode, TELEGRAM_TOKEN


if mode == "dev":

    def run(updater):
        updater.start_polling()
        updater.idle()

elif mode == "prod":

    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TELEGRAM_TOKEN,
                              webhook_url=f'https://{HEROKU_APP_NAME}'
                                          f'.herokuapp.com/{TELEGRAM_TOKEN}')
        updater.idle()

else:
    logger.error("No MODE specified!")
    sys.exit(1)


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel and end the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text("Всего доброго!",
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


if __name__ == "__main__":
    logger.info("Starting bot")
    updater = Updater(token=TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher

    # choosing_handler
    dispatcher.add_handler(get_choosing_handler())

    # person_data
    dispatcher.add_handler(get_handler_person())

    run(updater)
