import logging
import os
import sys
from enum import Enum, auto

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

# Enabling logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
load_dotenv()
mode = os.getenv("MODE", "dev")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


class StateEnum(Enum):
    CITY = auto()
    STORAGE = auto()


if mode == "dev":

    def run(updater):
        updater.start_polling()


elif mode == "prod":

    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TELEGRAM_TOKEN)
        updater.bot.set_webhook(
            "https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TELEGRAM_TOKEN)
        )


else:
    logger.error("No MODE specified!")
    sys.exit(1)


def keyboard_row_divider(full_list, row_width=2):
    """Divide list into rows for keyboard"""
    for i in range(0, len(full_list), row_width):
        yield full_list[i : i + row_width]


def start_handler(update: Update, context: CallbackContext):
    """Start conversation"""
    logger.info(f'User {update.effective_user["id"]} started bot')
    reply_keyboard = [["Москва"]]
    update.message.reply_text(
        "Привет! Я помогу тебе подобрать, забронировать и "
        "арендовать пространство для твоих вещей\nВыберите, "
        "пожалуйста, город:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Ваш город?",
            resize_keyboard=True,
        ),
    )
    return StateEnum.CITY


def city(update: Update, context: CallbackContext):
    """Handle city name"""
    city_name = update.message.text
    storages = [
        "Малая Бронная ул., 52",
        "Овчинниковская наб., 32",
        "Саринский пр-д, 26",
        "Мясницкая ул., 65",
    ]
    reply_keyboard = list(keyboard_row_divider(storages))

    update.message.reply_text(
        f"Выберете адрес хранилища в городе {city_name}:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Адрес хранилища",
            resize_keyboard=True,
        ),
    )
    return StateEnum.STORAGE


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text("Всего доброго!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


if __name__ == "__main__":
    logger.info("Starting bot")
    updater = Updater(token=TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            StateEnum.CITY: [MessageHandler(Filters.regex("^(Москва)$"), city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
