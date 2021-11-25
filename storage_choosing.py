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
    TYPE = auto()
    DIMENSION = auto()
    PERIOD = auto()


def get_storages() -> List[str]:
    """Give list of storages from DB"""
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


def get_types() -> List[str]:
    """Give types of possible things"""
    types = ['Сезонные вещи', 'Другое']
    return types


def get_dimension_cost(area: int) -> int:
    """Calculate cost of area"""
    first_meter = 599
    add_meter = 150
    return first_meter + add_meter * (area - 1)


def get_dimensions() -> List[str]:
    """Give dimensions for other things with cost"""
    dimensions = []
    for i in range(1, 11):
        cost = get_dimension_cost(i)
        dimensions.append(f"{i} кв.м.({cost} р.)")
    return dimensions


def get_periods() -> List[str]:
    """Give periods for Other"""
    periods = [f"{i} мес." for i in range(1, 13)]
    return periods


def send_period_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about period for Other things"""
    periods = get_periods()
    reply_keyboard = keyboard_row_divider(periods, 4)
    update.message.reply_text(
        "Выберите период хранения",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Период хранения",
            resize_keyboard=True,
        )
    )
    return StateEnum.PERIOD


def get_period(update: Update, context: CallbackContext) -> StateEnum:
    """Handle period for Other things"""
    period = update.message.text
    if period not in get_periods():
        update.message.reply_text("Простите столько мы не сможем хранить")
        return send_period_question(update, context)
    return ConversationHandler.END


def send_dimensions_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about dimensions for Other things"""
    dimensions = get_dimensions()
    reply_keyboard = keyboard_row_divider(dimensions, 3)
    update.message.reply_text(
        "Выберите габаритность ячейки",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Габаритность",
            resize_keyboard=True,
        )
    )
    return StateEnum.DIMENSION


def get_dimension(update: Update, context: CallbackContext) -> StateEnum:
    """Handle dimension of a box"""
    dimension = update.message.text
    if dimension not in get_dimensions():
        update.message.reply_text("Простите мы сдаем только целочисленную площадь")
        return send_dimensions_question(update, context)
    return send_period_question(update, context)


def send_type_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about type of things"""
    types = get_types()
    reply_keyboard = [types]
    update.message.reply_text(
        "Что хотите хранить?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Тип вещей",
            resize_keyboard=True,
        )
    )
    return StateEnum.TYPE


def get_type(update: Update, context: CallbackContext) -> StateEnum:
    """Handle type of things"""
    type_name = update.message.text
    if type_name not in get_types():
        update.message.reply_text("Простите, мы пока не храним такое :(")
        return send_type_question(update, context)
    if type_name == "Другое":
        return send_dimensions_question(update, context)
    return ConversationHandler.END


def send_storage_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about address of storage"""
    storages = get_storages()

    reply_keyboard = list(keyboard_row_divider(storages))
    update.message.reply_text(
        "Выберете адрес хранилища:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Адрес хранилища",
            resize_keyboard=True,
        ),
    )
    return StateEnum.STORAGE


def start_handler(update: Update, context: CallbackContext) -> StateEnum:
    """Start conversation and send first question"""
    logger.info(f'User {update.effective_user["id"]} started bot')
    update.message.reply_text(
        "Привет! Я помогу тебе подобрать, забронировать и "
        "арендовать пространство для твоих вещей")
    return send_storage_question(update, context)


def get_storage(update: Update, context: CallbackContext) -> StateEnum:
    """Handle storage address"""
    storage_name = update.message.text
    if storage_name not in get_storages():
        update.message.reply_text("Простите, по данному адресу у нас пока нет складов (")
        return send_storage_question(update, context)

    update.message.reply_text(
        f"Вы выбрали хранилище по адресу: {update.message.text}",
        reply_markup=ReplyKeyboardRemove()
    )
    return send_type_question(update, context)


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
            StateEnum.STORAGE: [MessageHandler(Filters.text, get_storage)],
            StateEnum.TYPE: [MessageHandler(Filters.text, get_type)],
            StateEnum.DIMENSION: [MessageHandler(Filters.text, get_dimension)],
            StateEnum.PERIOD: [MessageHandler(Filters.text, get_period)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
