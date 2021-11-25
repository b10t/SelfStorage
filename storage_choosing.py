from typing import List

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from enum import Enum, auto
import psycopg2
from load import logger, DATABASE_URL, keyboard_row_divider


class StateEnum(Enum):
    START = auto()
    STORAGE = auto()


def get_storages() -> List[str]:
    """Get list of storages from DB"""
    # connection = psycopg2.connect(DATABASE_URL)
    # cursor = connection.cursor()
    # cursor.execute("SELECT Address FROM storages")
    # storages_in_db = cursor.fetchall()
    # storages = []
    # for storage in storages_in_db:
    #     storages.append(''.join(storage))
    storages = ['test1', 'test2', 'test3', 'test4']
    # cursor.close()
    return storages


def storage_question(update: Update, context: CallbackContext) -> StateEnum:
    storages = get_storages()

    reply_keyboard = list(keyboard_row_divider(storages))
    update.message.reply_text(
        f"Выберете адрес хранилища:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Адрес хранилища",
            resize_keyboard=True,
        ),
    )
    return StateEnum.STORAGE


def start_handler(update: Update, context: CallbackContext) -> StateEnum:
    """Start conversation"""
    logger.info(f'User {update.effective_user["id"]} started bot')
    update.message.reply_text(
        "Привет! Я помогу тебе подобрать, забронировать и "
        "арендовать пространство для твоих вещей")
    return storage_question(update, context)


def storage(update: Update, context: CallbackContext) -> StateEnum:
    """Handle storage address"""
    storage_name = update.message.text
    if storage_name not in get_storages():
        update.message.reply_text(f"Простите, по данному адресу у нас пока нет складов (")
        return storage_question(update, context)

    update.message.reply_text(
        f"Вы выбрали хранилище по адресу: {update.message.text}",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel and end the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text("Всего доброго!",
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def get_choosing_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            StateEnum.START: [MessageHandler(Filters.text, start_handler)],
            StateEnum.STORAGE: [MessageHandler(Filters.text, storage)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
