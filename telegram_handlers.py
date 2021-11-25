from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update,
                      ForceReply)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


def start_person_data(update: Update, context: CallbackContext):
    """Start of receiving data on a person"""
    update.message.reply_text(
        'Необходимо ввести Ваши персональные данные:',
        reply_markup=ReplyKeyboardRemove()
    )
    update.message.reply_text(
        'Ваша фамилия:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='asdasd',
                                selective=True)
    )
    return 'user_name'


def get_user_name(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Ваше имя:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='asdasd',
                                selective=True)
    )
    return ConversationHandler.END


def get_middle_name(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Ваше отчество:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='asdasd',
                                selective=True)
    )
    return ConversationHandler.END


def get_telephone(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Ваше отчество:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='asdasd',
                                selective=True)
    )
    return ConversationHandler.END
