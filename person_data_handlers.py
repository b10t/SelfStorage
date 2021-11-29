import phonenumbers
from phonenumbers import NumberParseException
from phonenumbers.phonenumber import PhoneNumber
from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ParseMode, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler)

from load import DATABASE_URL, keyboard_row_divider, logger, escape_characters
from payment_handler import start_invoice


def set_person_info(person_data, user):
    """Установка данных человека."""
    if 'last_name' not in person_data:
        person_data['last_name'] = '`Введите фамилию`'
        if not user['last_name'] is None:
            person_data['last_name'] = user['last_name']

    if 'first_name' not in person_data:
        person_data['first_name'] = '`Введите имя`'
        if not user['first_name'] is None:
            person_data['first_name'] = user['first_name']

    if 'middle_name' not in person_data:
        person_data['middle_name'] = '`Введите отчество`'
        if not user['middle_name'] is None:
            person_data['middle_name'] = user['middle_name']

    if 'date_birth' not in person_data:
        person_data['date_birth'] = '`Введите дату рождения`'
        if not user['date_birth'] is None:
            person_data['date_birth'] = user['date_birth']

    if 'passport' not in person_data:
        person_data['passport'] = '`Введите данные паспорта`'
        if not user['passport'] is None:
            person_data['passport'] = user['passport']

    if 'telephone' not in person_data:
        person_data['telephone'] = '`Введите № телефона`'
        if not user['telephone'] is None:
            person_data['telephone'] = user['telephone']

    person_data['telephone'] = escape_characters(str(person_data['telephone']))


def acceptance_agreement(update: Update, context: CallbackContext):
    """Принятие соглашения по ПД."""
    inl_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('📄 Ознакомиться с соглашением',
                                     callback_data='AGREEMENT')],
            [
                InlineKeyboardButton('👍 Согласен',
                                     callback_data='YES'),
                InlineKeyboardButton('👎 Не согласен',
                                     callback_data='NO')
            ]
        ]
    )

    update.message.reply_text(
        '❗️*Внимание*❗️\n'
        '`Согласно требованиям Федерального закона от 27 июля 2006 г. № 152-ФЗ'
        '«О персональных данных» Вы должны дать согласие на'
        ' обработку персональных данных.`',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=inl_keyboard
    )
    return 'inline_button_agreement'


def inline_button_agreement(update: Update, context: CallbackContext):
    """Обработчик кнопок по работе с ПД."""
    bot = update.effective_message.bot
    query = update.callback_query

    if query.data == 'YES':
        return show_persion_data(update, context)
    elif query.data == 'NO':
        bot.answerCallbackQuery(
            callback_query_id=update.callback_query.id,
            text='⛔️ Бот не может продолжить с Вами работу'
                 ' без согласия на сбор ПД.',
            show_alert=True)
    elif query.data == 'AGREEMENT':
        with open('agreement.pdf', 'rb') as document:
            bot.send_document(
                chat_id=update._effective_chat.id,
                document=document)


def show_persion_data(update: Update, context: CallbackContext):
    """Отображает персональные данные человека."""
    if 'telephone' in dict(context.user_data):
        telephone = PhoneNumber()
        try:
            telephone = phonenumbers.parse(
                update.message.text, _check_region=False)
        except NumberParseException:
            pass

        if phonenumbers.is_valid_number(telephone):
            context.user_data['telephone'] = update.message.text
        else:
            update.message.reply_text('Вы ввели не правильный номер !',
                                      reply_markup=ReplyKeyboardRemove())
            return get_telephone(update, context)

    reply_keyboard = list(keyboard_row_divider(['Да', 'Нет']))

    set_person_info(context.user_data, update.effective_user)
    user_data = context.user_data

    update.effective_message.reply_text(
        f"_Ваши персональные данные_:\n"
        f"*Фамилия:* `{user_data['last_name']}`\n"
        f"*Имя:* `{user_data['first_name']}`\n"
        f"*Отчество:* `{user_data['middle_name']}`\n"
        f"*Дата рождения:* `{user_data['date_birth']}`\n"
        f"*Паспорт:* `{user_data['passport']}`\n"
        f"*☎️:* `{user_data['telephone']}`\n",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Данные верны ?',
            resize_keyboard=True,)
    )

    return 'process_answer_yes_no'


def process_answer_yes_no(update: Update, context: CallbackContext):
    """Обработчик кнопок по правильности введённых данных."""
    text = update.message.text

    if text == 'Да':
        update.message.reply_text('Данные приняты !\nМожно переходить к оплате',
                                  reply_markup=ReplyKeyboardRemove())

        del context.user_data['telephone']
        start_invoice(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Ваша фамилия:',
            reply_markup=ForceReply(force_reply=True,
                                    input_field_placeholder='Фамилия',
                                    selective=True)
        )
        # TODO вернуть get_surname
        return 'get_passport'


def get_surname(update: Update, context: CallbackContext):
    """Получение фамилии."""
    update.message.reply_text(
        'Ваша фамилия:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Фамилия',
                                selective=True)
    )
    return 'get_user_name'


def get_user_name(update: Update, context: CallbackContext):
    """Получение имени."""
    context.user_data['last_name'] = update.message.text
    update.message.reply_text(
        'Ваше имя:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Имя',
                                selective=True)
    )
    return 'get_middle_name'


def get_middle_name(update: Update, context: CallbackContext):
    """Получение отчества."""
    context.user_data['first_name'] = update.message.text
    update.message.reply_text(
        'Ваше отчество:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Отчество',
                                selective=True)
    )
    return 'get_date_birth'


def get_date_birth(update: Update, context: CallbackContext):
    """Получение даты рождения."""
    context.user_data['middle_name'] = update.message.text
    update.message.reply_text(
        'Дата рождения:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='01.22.1900',
                                selective=True)
    )
    return 'get_passport'


def get_passport(update: Update, context: CallbackContext):
    """Получение данных паспорта."""
    context.user_data['date_birth'] = update.message.text
    update.message.reply_text(
        'Данные паспорта:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='XX XX YYYYYY',
                                selective=True)
    )
    return 'select_input_phone'


def select_input_phone(update: Update, context: CallbackContext):
    """Отображение способа получения номера телефона."""
    context.user_data['passport'] = update.message.text

    enter_phone = KeyboardButton('Ввести номер вручную ☎️',
                                 request_contact=False)
    send_phone = KeyboardButton('Отправить свой контакт ☎️',
                                request_contact=True)

    reply_keyboard = list(keyboard_row_divider([enter_phone, send_phone], 1))

    update.message.reply_text(
        'Каким способом ввести номер телефона ?',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='',
            resize_keyboard=True,)
    )

    return 'get_telephone'


def get_telephone(update: Update, context: CallbackContext):
    """Получение номера телефона."""
    contact = update.effective_message.contact
    if contact:
        contact = update.effective_message.contact
        update.message.text = contact.phone_number
        return show_persion_data(update, context)

    update.message.reply_text(
        'Ваш телефон:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Телефон',
                                selective=True)
    )
    return 'show_persion_data'


def get_handler_person():
    """Возвращает обработчик разговоров."""
    return ConversationHandler(
        entry_points=[MessageHandler(
            Filters.regex('^Подтверждаю$'),
            acceptance_agreement)],
        states={
            "inline_button_agreement": [
                CallbackQueryHandler(
                    inline_button_agreement
                )
            ],
            "show_persion_data": [
                MessageHandler(
                    Filters.text,
                    show_persion_data
                )
            ],
            "get_surname": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_surname
                )
            ],
            "get_user_name": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_user_name
                )
            ],
            "get_middle_name": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_middle_name
                )
            ],
            "get_date_birth": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_date_birth
                )
            ],
            "get_passport": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_passport
                )
            ],
            "select_input_phone": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    select_input_phone
                )
            ],
            "get_telephone": [
                MessageHandler(
                    (Filters.text | Filters.contact) & ~Filters.command,
                    get_telephone
                )
            ],
            "process_answer_yes_no": [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    process_answer_yes_no
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", acceptance_agreement)]
    )
