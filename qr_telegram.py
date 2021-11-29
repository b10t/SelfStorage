from pyqrcode import QRCode
import os
import png

from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update, KeyboardButton)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          PreCheckoutQueryHandler, MessageHandler)


def get_qr_code(update: Update, context: CallbackContext) -> None:
    """get qr code for text_in_code"""
    text_in_code = [
        context.user_data['last_name'],
        context.user_data['first_name'],
        context.user_data['storage'],
        context.user_data['type'],
        str(context.user_data['invoice_price'])
    ]
    message_id = update.message.message_id
    text = ' '.join(text_in_code)
    qr = QRCode(text)
    qr.png('code.png', scale=10)
    update.message.reply_photo(
        photo=open('code.png', 'rb'),
        reply_to_message_id=message_id,
        caption='Ваш QR-код для входа в хранилище')
    os.remove('code.png')


def add_qr_handlers(dispatcher) -> None:
    dispatcher.add_handler(CommandHandler(
        "qr", get_qr_code))
