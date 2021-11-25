from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      ForceReply, ParseMode)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


def keyboard_row_divider(full_list, row_width=2):
    """Divide list into rows for keyboard"""
    for i in range(0, len(full_list), row_width):
        yield full_list[i: i + row_width]


def set_person_info(person_data, user):
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

    if 'telephone' not in person_data:
        person_data['telephone'] = '`Введите № телефона`'
        if not user['telephone'] is None:
            person_data['telephone'] = user['telephone']


def show_persion_data(update: Update, context: CallbackContext):
    """[summary]

    Args:
        update (Update): [description]
        context (CallbackContext): [description]
    """
    if 'telephone' in dict(context.user_data):
        context.user_data['telephone'] = update.message.text

    reply_keyboard = list(keyboard_row_divider(["Да", "Нет"]))

    set_person_info(context.user_data, update.message.from_user)
    user_data = context.user_data

    update.message.reply_text(
        f"""_Ваши персональные данные_:
*Фамилия:* {user_data['last_name']}
*Имя:* {user_data['first_name']}
*Отчество:* {user_data['middle_name']}
*☎️:* {user_data['telephone']}""",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Данные верны ?",
            resize_keyboard=True,)
    )

    return 'process_answer_yes_no'


def process_answer_yes_no(update: Update, context: CallbackContext):
    text = update.message.text

    if text == 'Да':
        update.message.reply_text("Данные приняты !",
                                  reply_markup=ReplyKeyboardRemove())

        del context.user_data['telephone']

        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Ваша фамилия:',
            reply_markup=ForceReply(force_reply=True,
                                    input_field_placeholder='Фамилия',
                                    selective=True)
        )
        return 'get_user_name'


def get_surname(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Ваша фамилия:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Фамилия',
                                selective=True)
    )
    return 'get_user_name'


def get_user_name(update: Update, context: CallbackContext):
    context.user_data['last_name'] = update.message.text
    update.message.reply_text(
        'Ваше имя:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Имя',
                                selective=True)
    )
    return 'get_middle_name'


def get_middle_name(update: Update, context: CallbackContext):
    context.user_data['first_name'] = update.message.text
    update.message.reply_text(
        'Ваше отчество:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Отчество',
                                selective=True)
    )
    return 'get_telephone'


def get_telephone(update: Update, context: CallbackContext):
    context.user_data['middle_name'] = update.message.text
    # markup_request = ReplyKeyboardMarkup(resize_keyboard=True).add(
    #     KeyboardButton('Отправить свой контакт ☎️', request_contact=True)
    # ).add(
    #     KeyboardButton('Отправить свою локацию 🗺️', request_location=True)
    # )

    update.message.reply_text(
        'Ваш телефон:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Телефон',
                                selective=True)
    )
    return 'show_persion_data'


def successful_person_data_entry(update: Update, context: CallbackContext):
    context.user_data['telephone'] = update.message.text

    # update.message.reply_text(
    #     "Данные успешно введены !",
    #     reply_markup=ReplyKeyboardRemove()
    # )
    return 'show_persion_data'


def end_step_person_data(update: Update, context: CallbackContext):
    return ConversationHandler.END


def get_handler_person():
    return ConversationHandler(
        entry_points=[CommandHandler("person_data", show_persion_data)],
        states={
            "get_surname": [MessageHandler(Filters.text, get_surname)],
            "get_user_name": [MessageHandler(Filters.text, get_user_name)],
            "get_middle_name": [MessageHandler(Filters.text, get_middle_name)],
            "get_telephone": [MessageHandler(Filters.text, get_telephone)],
            "process_answer_yes_no": [MessageHandler(Filters.text, process_answer_yes_no)],
            "end_step_person_data": [MessageHandler(Filters.text, process_answer_yes_no)],
            "show_persion_data": [MessageHandler(Filters.text, show_persion_data)],
            "successful_person_data_entry": [MessageHandler(Filters.text, successful_person_data_entry)],
            # "evaluation": [MessageHandler(Filters.regex('1|2|3|4|5'), anketa_get_evaluation)],
            # "comment": [MessageHandler(Filters.regex('Пропустить'), anketa_exit_comment),
            #             MessageHandler(Filters.text, anketa_comment)],
        },
        fallbacks=[CommandHandler("cancel", show_persion_data)]
    )
