from enum import Enum, auto
from typing import List
from datetime import date, timedelta
from geopy.distance import geodesic

import psycopg2
from telegram import (ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update, KeyboardButton)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler)

from load import DATABASE_URL, keyboard_row_divider, logger, escape_characters
from person_data_handlers import get_handler_person


class StateEnum(Enum):
    LOCATE = auto()
    STORAGE = auto()
    TYPE = auto()
    DIMENSION = auto()
    PERIOD = auto()
    SEASONAL = auto()
    COUNT = auto()
    PERIOD_TYPE = auto()
    PERIOD_COUNT = auto()
    PROMO = auto()
    CHANGE_PERIOD = auto()
    PERSON_DATA = auto()


def clear_user_data(update: Update, context: CallbackContext) -> None:
    context.user_data['storage'] = None
    context.user_data['type'] = None
    context.user_data['dimension'] = None
    context.user_data['other_period'] = None
    context.user_data['seasonal'] = None
    context.user_data['count'] = None
    context.user_data['locate'] = None
    context.user_data['period_type'] = None
    context.user_data['period_count'] = None
    context.user_data['invoice_description'] = None
    context.user_data['invoice_price'] = None
    context.user_data['invoice_discount'] = None
    context.user_data['discount'] = None
    context.user_data['promo'] = None


def get_storages() -> [List[str],List[str]]:
    """Give list of storages from DB"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT Address, Latitude, Longitude  FROM storages')
    storages_data = cursor.fetchall()
    storages = [x[0] for x in storages_data]
    cursor.close()
    return storages,storages_data


def get_types() -> List[str]:
    """Give types of possible things"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT Name FROM typecell WHERE id=1 or id=2')
    types = [x[0] for x in cursor.fetchall()]

    cursor.close()
    return types


def get_dimension_cost(area: int) -> int:
    """Calculate cost of area"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT cost1 FROM typecell WHERE id=2')
    first_meter = float(cursor.fetchone()[0])
    cursor.execute('SELECT cost2 FROM typecell WHERE id=2')
    add_meter = float(cursor.fetchone()[0])
    cursor.close()
    return first_meter + add_meter * (area - 1)


def get_dimensions() -> List[str]:
    """Give dimensions for other things with cost"""
    dimensions = []
    for i in range(1, 11):
        cost = get_dimension_cost(i)
        dimensions.append(f'{i} кв.м.({cost} р.)')
    return dimensions


def clear_dimension(full_name: str) -> int:
    """Clear dimension phrase"""
    return int(full_name.split(' ')[0])


def get_periods() -> List[str]:
    """Give periods for Other"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT periodmin FROM typecell WHERE id=2')
    min_period = int(cursor.fetchone()[0]) // 4
    cursor.execute('SELECT periodmax FROM typecell WHERE id=2')
    max_period = int(cursor.fetchone()[0]) // 4
    cursor.close()
    periods = [f'{i} мес.' for i in range(min_period, max_period + 1)]
    return periods


def clear_period(full_name: str) -> int:
    """Clear period phrase"""
    return int(full_name.split(' ')[0])


def get_seasonal_cost(seasonal: str) -> [int, int]:
    """Give cost for seasonal for a week and month in one tuple"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT name, cost1, cost2 FROM typecell')
    type_cells = cursor.fetchall()
    cursor.close()
    for type_cell in type_cells:
        if seasonal == type_cell[0]:
            return type_cell[1],type_cell[2]


def get_seasonals() -> List[str]:
    """Give seasonal types of things"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM typecell WHERE id > 2')
    seasonals =  [x[0] for x in cursor.fetchall()]
    cursor.close()
    return seasonals


def get_seasonals_week() -> List[str]:
    """Give seasonals for choice week or month long"""
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM typecell WHERE cost1 is not Null AND id>2')
    seasonals = [x[0] for x in cursor.fetchall()]
    cursor.close()
    return seasonals


def get_period_types() -> List[str]:
    """Give period types for seasonal things"""
    period_types = ['Месяцы', 'Недели']
    return period_types


def get_period_counts(period_type: str) -> List[str]:
    """Give period counts for seasonal things"""
    if period_type == 'Недели':
        period_counts = [f'{i} нед.' for i in range(1, 4)]
    else:
        period_counts = [f'{i} мес.' for i in range(1, 7)]
    return period_counts


def clear_period_count(full_name: str) -> int:
    """Clear period count phrase"""
    return int(full_name.split(' ')[0])


def get_promos() -> dict[str, float]:
    """Give all promos"""
    promos = {'storage2022': 0.2, 'storage15': 0.15, 'Нет Промокода :(': 0}
    return promos


def send_full_price(update: Update, context: CallbackContext) -> StateEnum:
    """Send calculation of full price"""
    storage = context.user_data['storage']
    things_type = context.user_data['type']
    discount = context.user_data['discount']
    result_answer = f'Мы подготовим для Вас пространство:\nПо адресу: *{storage}*\n'
    invoice_description = f'Адрес: "{storage}"\n'
    full_cost = None
    period_start = date.today()
    period_end = None
    if things_type == 'Другое':
        dimension = context.user_data['dimension']
        other_period = context.user_data['other_period']
        full_cost = get_dimension_cost(dimension) * other_period
        full_cost_discount = full_cost * (1 - discount)
        period_end = date.today() + timedelta(days=other_period * 4 * 7)
        result_answer += (
            f'Для хранения: *{things_type}*\n'
            f'Размером в *{dimension}* кв.м.\n'
            f'На период в *{other_period}* мес.\n'
            f'Стоимость без скидки: *{full_cost:.2f}* рублей \n'
            f'Итоговая стоимость составляет: *{full_cost_discount:.2f}* рублей'
        )
        invoice_description += f'Площадь: {dimension} кв.м.\n'

    if things_type == 'Сезонные вещи':
        seasonal = context.user_data['seasonal']
        count = int(context.user_data['count'])
        cost = get_seasonal_cost(seasonal)
        period_type = context.user_data['period_type']
        period_count = int(context.user_data['period_count'])
        if period_type == 'Недели':
            period_name = 'нед'
            full_cost = cost[0] * period_count * count
            period_end = date.today() + timedelta(days=period_count * 7)
        else:
            period_name = 'мес'
            full_cost = cost[1] * period_count * count
            period_end = date.today() + timedelta(days=period_count * 4 * 7)
        full_cost_discount = full_cost * (1 - discount)
        result_answer += (
            f'Для хранения вещей вида *{seasonal}*\n'
            f'В количестве *{count}* штук\n'
            f'На период *{period_count} {period_name}*\n'
            f'Стоимость без скидки: *{full_cost:.2f}* рублей \n'
            f'Итоговая стоимость составляет: *{full_cost_discount:.2f}* рублей'
        )
        invoice_description += f'Храним: "{seasonal}"\n' \
                               f'Количество: {count} штук\n'

    invoice_description += f'Период хранения ' \
                           f'c {period_start.strftime("%d.%m.%Y")} ' \
                           f'по {period_end.strftime("%d.%m.%Y")}'

    context.user_data['invoice_description'] = invoice_description
    context.user_data['invoice_price'] = full_cost
    context.user_data['invoice_discount'] = discount
    update.message.reply_text(
        escape_characters(result_answer),
        reply_markup=ReplyKeyboardMarkup(
            [['Подтверждаю']],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    return StateEnum.PERSON_DATA


def send_promo_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about promo"""
    if context.user_data['promo']:
        return get_promo(update, context)
    update.message.reply_text(
        'Промокод на скидку',
        reply_markup=ReplyKeyboardMarkup(
            [['Нет Промокода :(']],
            one_time_keyboard=True,
            input_field_placeholder='Промокод',
            resize_keyboard=True,
        ),
    )
    return StateEnum.PROMO


def get_promo(update: Update, context: CallbackContext) -> StateEnum:
    """Handle promo"""
    promo = update.message.text
    if context.user_data['promo']:
        promo = context.user_data['promo']
    all_promos = get_promos()
    if context.user_data['period_count']:
        period_count = int(context.user_data['period_count'])
        period_type = context.user_data['period_type']
    else:
        period_count = int(context.user_data['other_period'])
        period_type = 'Месяцы'
    promo_err = ''

    if promo not in all_promos:
        update.message.reply_text('Простите, срок действия данного промокода истек')
        return send_promo_question(update, context)

    promo_length = period_count
    if period_type == 'Месяцы':
        promo_length = period_count*4
    if promo_length < 12 and promo == 'storage2022':
        promo_err = 'Промокод начинает действовать от аренды на 3 месяцы и более, ' \
                    'хотите сменить продолжительность аренды?'
    if promo_length > 8 and promo == 'storage15':
        promo_err = 'Промокод работает на срок до 2х месяцев включительно, ' \
                    'хотите сменить продолжительность аренды?'
    if promo_err:
        context.user_data['promo'] = promo
        update.message.reply_text(
            promo_err,
            reply_markup=ReplyKeyboardMarkup(
                [['Да', 'Нет']],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),)
        return StateEnum.CHANGE_PERIOD

    discount = all_promos.get(promo)
    context.user_data['discount'] = discount
    update.message.reply_text(f'Ваша скидка составляет {discount*100}%')
    return send_full_price(update, context)


def send_period_count_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about number of periods for seasonal things"""
    period_type = context.user_data['period_type']
    period_counts = get_period_counts(period_type)
    reply_keyboard = keyboard_row_divider(period_counts, 3)
    update.message.reply_text(
        'Выберите срок хранения Ваших вещей',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Срок хранения',
            resize_keyboard=True,
        ),
    )
    return StateEnum.PERIOD_COUNT


def get_period_count(update: Update, context: CallbackContext) -> StateEnum:
    """Handle number of periods for seasonal items"""
    period_count = update.message.text
    period_type = context.user_data['period_type']
    if period_count not in get_period_counts(period_type):
        update.message.reply_text('Простите, мы не храним столько')
        return send_period_count_question(update, context)

    context.user_data['period_count'] = clear_period_count(period_count)
    return send_promo_question(update, context)


def get_change_period(update: Update, context: CallbackContext) -> StateEnum:
    """Handle changing period"""
    will_change = update.message.text
    if will_change == 'Да':
        return send_period_count_question(update, context)

    return send_full_price(update, context)


def send_period_type_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about period type of seasonal things"""
    period_types = get_period_types()
    reply_keyboard = [period_types]
    update.message.reply_text(
        'Напишите единицу измерения срока хранения вещей',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Месяцы или недели',
            resize_keyboard=True,
        ),
    )
    return StateEnum.PERIOD_TYPE


def get_period_type(update: Update, context: CallbackContext) -> StateEnum:
    """Handle period type for seasonal things"""
    period_type = update.message.text
    if period_type not in get_period_types():
        update.message.reply_text('Простите, мы не храним столько')
        return send_period_type_question(update, context)

    context.user_data['period_type'] = period_type
    return send_period_count_question(update, context)


def send_seasonal_cost(update: Update, context: CallbackContext) -> StateEnum:
    """Send week/month cost of seasonal items"""
    seasonal = context.user_data['seasonal']
    count = int(context.user_data['count'])
    cost = get_seasonal_cost(seasonal)
    if seasonal in get_seasonals_week():
        update.message.reply_text(
            f'Стоимость хранения вещей '
            f'вида "{seasonal}" в количестве {count} шт. \n'
            f'составляет {cost[0]*count} р/неделя или {cost[1]*count} р/мес'
        )
        return send_period_type_question(update, context)
    else:
        update.message.reply_text(
            f'Стоимость хранения вещей '
            f'вида "{seasonal}" в количестве {count} шт. \n'
            f'составляет {cost[1]*count} р/мес'
        )
        context.user_data['period_type'] = 'Месяцы'
        return send_period_count_question(update, context)


def send_count_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about count of seasonal things"""
    update.message.reply_text(
        f'Введите количество вещей вида {context.user_data["seasonal"]}',
        reply_markup=ReplyKeyboardRemove(),
    )
    return StateEnum.COUNT


def get_count(update: Update, context: CallbackContext) -> StateEnum:
    """Handle count of seasonal things"""
    count = update.message.text
    if not count.isnumeric():
        update.message.reply_text(
            'Простите, мы храним только целое количество вещей')
        return send_count_question(update, context)

    context.user_data['count'] = count
    return send_seasonal_cost(update, context)


def send_seasonal_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about seasonal type of things"""
    seasonals = get_seasonals()
    reply_keyboard = keyboard_row_divider(seasonals, 2)
    update.message.reply_text(
        'Выберите вид вещей для хранения',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Вид сезонных вещей',
            resize_keyboard=True,
        ),
    )
    return StateEnum.SEASONAL


def get_seasonal(update: Update, context: CallbackContext) -> StateEnum:
    """Handle type of seasonal things"""
    seasonal = update.message.text
    if seasonal not in get_seasonals():
        update.message.reply_text(
            'Простите, такой вид вещей мы пока не храним')
        return send_seasonal_question(update, context)

    context.user_data['seasonal'] = seasonal
    return send_count_question(update, context)


def send_period_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about period for Other things"""
    periods = get_periods()
    reply_keyboard = keyboard_row_divider(periods, 4)
    update.message.reply_text(
        'Выберите период хранения',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Период хранения',
            resize_keyboard=True,
        ),
    )
    return StateEnum.PERIOD


def get_period(update: Update, context: CallbackContext) -> StateEnum:
    """Handle period for Other things"""
    period = update.message.text
    if period not in get_periods():
        update.message.reply_text('Простите, столько мы не сможем хранить')
        return send_period_question(update, context)

    context.user_data['other_period'] = clear_period(period)
    return send_promo_question(update, context)


def send_dimensions_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about dimensions for Other things"""
    dimensions = get_dimensions()
    reply_keyboard = keyboard_row_divider(dimensions, 3)
    update.message.reply_text(
        'Выберите габаритность ячейки',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Габаритность',
            resize_keyboard=True,
        ),
    )
    return StateEnum.DIMENSION


def get_dimension(update: Update, context: CallbackContext) -> StateEnum:
    """Handle dimension of a box"""
    dimension = update.message.text
    if dimension not in get_dimensions():
        update.message.reply_text(
            'Простите, мы сдаем только целочисленную площадь')
        return send_dimensions_question(update, context)

    context.user_data['dimension'] = clear_dimension(dimension)
    return send_period_question(update, context)


def send_type_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about type of things"""
    types = get_types()
    reply_keyboard = [types]
    update.message.reply_text(
        'Что хотите хранить?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Тип вещей',
            resize_keyboard=True,
        ),
    )
    return StateEnum.TYPE


def get_type(update: Update, context: CallbackContext) -> StateEnum:
    """Handle type of things"""
    type_name = update.message.text
    if type_name not in get_types():
        update.message.reply_text('Простите, мы пока не храним такое :(')
        return send_type_question(update, context)
    if type_name == 'Другое':
        context.user_data['type'] = type_name
        return send_dimensions_question(update, context)
    if type_name == 'Сезонные вещи':
        context.user_data['type'] = type_name
        return send_seasonal_question(update, context)

    return ConversationHandler.END


def send_locate_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about get locate"""
    get_locate_yes = KeyboardButton(
        'Да', request_location=True)

    get_locate_no = KeyboardButton(
        'Нет')

    reply_keyboard = list(keyboard_row_divider(
        [get_locate_yes, get_locate_no], 2))

    update.message.reply_text(
        'Хотите определить расстояние до складов ?',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='',
            resize_keyboard=True,)
    )

    return StateEnum.LOCATE


def get_locate(update: Update, context: CallbackContext):
    """Handle locate"""

    user_location = update.message.location
    if user_location:
        context.user_data['locate'] = user_location
        logger.info("Поле locate",context.user_data['locate'])

    return send_storage_question(update, context)

def get_storage_distance(coord_user, storages_data) -> List[float]:
    """give a list of distances to storages"""
    distances=[]
    origin= (coord_user.latitude,coord_user.longitude)
    for storage in storages_data:
        distances.append(geodesic(origin, (storage[1],storage[2])).kilometers)
    return distances

def send_storage_question(update: Update, context: CallbackContext) -> StateEnum:
    """Send question about address of storage"""
    storages, storages_data = get_storages()
    if context.user_data['locate']:
        distances=get_storage_distance(context.user_data['locate'], storages_data)
        i=0
        for x in storages_data:
            storages[i] = f'{x[0]} ({distances[i]:.1f} км)'
            i+=1
    reply_keyboard = list(keyboard_row_divider(storages))
    update.message.reply_text(
        'Выберете адрес хранилища:',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Адрес хранилища',
            resize_keyboard=True,
        ),
    )
    return StateEnum.STORAGE


def start_handler(update: Update, context: CallbackContext) -> StateEnum:
    """Start conversation and send first question"""
    logger.info(f'User {update.effective_user["id"]} started bot')
    update.message.reply_text(
        'Привет! Я помогу Вам подобрать, забронировать и '
        'арендовать пространство для твоих вещей'
    )

    clear_user_data(update, context)
    return send_locate_question(update, context)
    #return send_storage_question(update, context)


def get_storage(update: Update, context: CallbackContext) -> StateEnum:
    """Handle storage address"""
    storage_name = update.message.text
    if storage_name not in get_storages()[0]:
        update.message.reply_text(
            'Простите, по данному адресу у нас пока нет складов ('
        )
        return send_storage_question(update, context)

    context.user_data['storage'] = storage_name
    return send_type_question(update, context)


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel and end the conversation."""
    user = update.message.from_user
    logger.info('User %s canceled the conversation.', user.first_name)
    update.message.reply_text(
        'Всего доброго!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Confirm the successful payment."""
    update.message.reply_text("Спасибо, что пользуетесь нашим сервисом!")


def get_choosing_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],
        states={
            StateEnum.LOCATE: [MessageHandler((Filters.text | Filters.location) & ~Filters.command, get_locate)],
            StateEnum.STORAGE: [MessageHandler(Filters.text & ~Filters.command, get_storage)],
            StateEnum.TYPE: [MessageHandler(Filters.text & ~Filters.command, get_type)],
            StateEnum.DIMENSION: [MessageHandler(Filters.text & ~Filters.command, get_dimension)],
            StateEnum.PERIOD: [MessageHandler(Filters.text & ~Filters.command, get_period)],
            StateEnum.SEASONAL: [MessageHandler(Filters.text & ~Filters.command, get_seasonal)],
            StateEnum.COUNT: [MessageHandler(Filters.text & ~Filters.command, get_count)],
            StateEnum.PERIOD_TYPE: [MessageHandler(Filters.text & ~Filters.command, get_period_type)],
            StateEnum.PERIOD_COUNT: [MessageHandler(Filters.text & ~Filters.command, get_period_count)],
            StateEnum.PROMO: [MessageHandler(Filters.text & ~Filters.command, get_promo)],
            StateEnum.CHANGE_PERIOD: [MessageHandler(Filters.text & ~Filters.command, get_change_period)],
            StateEnum.PERSON_DATA: [get_handler_person()]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(Filters.successful_payment, successful_payment_callback)],
    )
