import logging
import os
import random
import sys

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Updater, CallbackContext
from telegram import Update

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
load_dotenv()
mode = os.getenv("MODE")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TELEGRAM_TOKEN,
                              webhook_url = f'https://{HEROKU_APP_NAME}.herokuapp.com/{TELEGRAM_TOKEN}')
        updater.idle()
else:
    logger.error("No MODE specified!")
    sys.exit(1)


def start_handler(update: Update, context: CallbackContext):
    # Creating a handler-function for /start command
    logger.info(f'User {update.effective_user["id"]} started bot')
    update.message.reply_text(
        "Hello from Python!\nPress /random to get random number")


def random_handler(update: Update, context: CallbackContext):
    # Creating a handler-function for /random command
    number = random.randint(0, 10)
    logger.info(f'User {update.effective_user["id"]} randomed number {number}')
    update.message.reply_text("Random number: {}".format(number))


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(token=TELEGRAM_TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    updater.dispatcher.add_handler(CommandHandler("random", random_handler))

    run(updater)
