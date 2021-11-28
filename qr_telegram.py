from pyqrcode import QRCode
import os
import png
from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update, KeyboardButton)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler)


def get_qr_code(update: Update, context: CallbackContext,text_in_code:list) -> None:
    """get qr code for text_in_code"""
    message_id = update.message.message_id
    text = ' '.join(text_in_code)
    qr = QRCode(text)
    qr.png('code.png', scale=10)
    update.message.reply_photo(photo=open(
        'code.png', 'rb'), reply_to_message_id=message_id, caption=f'Ваш QR-код для входа в хранилище')
    os.remove('code.png')


if __name__=='__main__':
    get_qr_code(["Клиент 5 ","Ячейка 7"])