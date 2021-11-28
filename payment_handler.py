from telegram import LabeledPrice, Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    PreCheckoutQueryHandler,
    CallbackContext,
)

from load import PROVIDER_TOKEN


def start_without_shipping_callback(update: Update, context: CallbackContext) -> None:
    """Send an invoice"""
    chat_id = update.message.chat_id
    title = "Аренда площади"
    description = context.user_data['invoice_description']
    payload = "PayloadBot22"
    provider_token = PROVIDER_TOKEN
    currency = "rub"
    price = int(context.user_data['invoice_price'])
    prices = [LabeledPrice("Аренда склада", price * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    """Answer the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    if query.invoice_payload != 'PayloadBot22':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Confirms the successful payment."""
    update.message.reply_text("Спасибо, что пользуетесь нашим сервисом!")


def add_payment_handlers(dispatcher) -> None:
    dispatcher.add_handler(CommandHandler("payme", start_without_shipping_callback))

    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))
