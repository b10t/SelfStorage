import os
from builtins import getattr

import png
from pyqrcode import QRCode
from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ParseMode, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          PreCheckoutQueryHandler)


def get_qr_code(update: Update, context: CallbackContext) -> int:
    """get qr code for text_in_code"""
    text_in_code = [
        context.user_data['last_name'],
        context.user_data['first_name'],
        context.user_data['storage'],
        context.user_data['type'],
        str(context.user_data['invoice_price'])
    ]
    message_id = update.message.message_id
    text = ''.join(str(text_in_code))
    qr = QRCode(text, encoding='utf8')
    qr.png('code.png', scale=10)
    update.message.reply_photo(
        photo=open('code.png', 'rb'),
        reply_to_message_id=message_id,
        caption='Ваш QR-код для входа в хранилище')
    os.remove('code.png')

    return ConversationHandler.END


def add_qr_handlers(dispatcher) -> None:
    dispatcher.add_handler(CommandHandler(
        "qr", get_qr_code))
