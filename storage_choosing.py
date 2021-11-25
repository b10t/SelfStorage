from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from enum import Enum, auto
import psycopg2
from load import logger, DATABASE_URL, keyboard_row_divider


class StateEnum(Enum):
    CITY = auto()
    STORAGE = auto()


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
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute("SELECT Address FROM storages")
    storages_in_db = cursor.fetchall()
    storages = []
    for storage in storages_in_db:
        storages.append(''.join(storage))
    city_name = update.message.text

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
    # cursor.close()
    return StateEnum.STORAGE


def storage(update: Update, context: CallbackContext):
    """Handle storage address"""
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
            StateEnum.CITY: [
                MessageHandler(
                    Filters.regex("^(Москва)$"),
                    city)],
            StateEnum.STORAGE: [MessageHandler(Filters.text, storage)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
