import os
import sys

from telegram.ext import Updater

from payment_handler import add_payment_handlers
from storage_choosing import get_choosing_handler
from person_data_handlers import get_handler_person
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


if __name__ == "__main__":
    logger.info("Starting bot")
    updater = Updater(token=TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher

    # choosing_handler
    dispatcher.add_handler(get_choosing_handler())

    # person_data
    dispatcher.add_handler(get_handler_person())

    add_payment_handlers(dispatcher)

    run(updater)
