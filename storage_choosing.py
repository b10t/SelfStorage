from typing import List

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ParseMode
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
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute("SELECT Address FROM storages")
    storages = [x[0] for x in cursor.fetchall()]
    """
    storages = [
        'Новый Арбат ул., 38',
        'Гагаринский пер., 85',
        'Климентовский пер., 79',
        'Таганская ул., 71'
    ]"""
    cursor.close()
    return storages


def get_types() -> List[str]:
    """Give types of possible things"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute("SELECT Name FROM typecell WHERE id=1 or id=2")
    types = [x[0] for x in cursor.fetchall()]

    #types = ['Сезонные вещи', 'Другое']
    cursor.close()
    return types


def get_dimension_cost(area: int) -> int:
    """Calculate cost of area"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute("SELECT cost1 FROM typecell WHERE id=2")
    first_meter = float(cursor.fetchone()[0])
    cursor.execute("SELECT cost2 FROM typecell WHERE id=2")
    add_meter = float(cursor.fetchone()[0])
    cursor.close()
    return first_meter + add_meter * (area - 1)


def get_dimensions() -> List[str]:
    """Give dimensions for other things with cost"""
    dimensions = []
    for i in range(1, 11):
        cost = get_dimension_cost(i)
        dimensions.append(f"{i} кв.м.({cost} р.)")
    return dimensions


def clear_dimension(full_name: str) -> int:
    """Clear dimension phrase"""
    return int(full_name.split(' ')[0])


def get_periods() -> List[str]:
    """Give periods for Other"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute("SELECT periodmin FROM typecell WHERE id=2")
    min_period = int(cursor.fetchone()[0]) // 4
    cursor.execute("SELECT periodmax FROM typecell WHERE id=2")
    max_period = int(cursor.fetchone()[0]) // 4
    cursor.close()
    periods = [f"{i} мес." for i in range(min_period, max_period+1)]
    return periods


def clear_period(full_name: str) -> int:
    """Clear period phrase"""
    return int(full_name.split(' ')[0])


def send_full_price(update: Update, context: CallbackContext) -> StateEnum:
    """Send calculation of full price"""
    storage = context.user_data['storage'].replace('.', '\.')
    things_type = context.user_data['type']
    dimension = context.user_data['dimension']
    other_period = context.user_data['other_period']
    full_cost = get_dimension_cost(dimension) * other_period
    update.message.reply_text(
        f'Мы подготовим для вас пространство:\n'
        f'По адресу: *{storage}*\n'
        f'Для хранения: *{things_type}*\n'
        f'Размером в *{dimension}* кв\.м\.\n'
        f'На период в *{other_period}* мес\.\n'
        f'Общая стоимость составляет: *{full_cost}* рублей',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return ConversationHandler.END


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

    context.user_data['other_period'] = clear_period(period)
    return send_full_price(update, context)


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

    context.user_data['dimension'] = clear_dimension(dimension)
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
        context.user_data['type'] = type_name
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
    context.user_data['storage'] = storage_name
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


