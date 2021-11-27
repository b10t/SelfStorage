#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""Basic example for a bot that can receive payment from user."""

import logging

from telegram import LabeledPrice, ShippingOption, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    CallbackContext,
)

from load import logger, PROVIDER_TOKEN


def start_without_shipping_callback(update: Update, context: CallbackContext) -> None:
    """Send an invoice"""
    chat_id = update.message.chat_id
    title = "Аренда площади"
    description = "Payment Example using python-telegram-bot"
    payload = "PayloadBot22"
    provider_token = PROVIDER_TOKEN
    currency = "USD"
    price = 1200
    prices = [LabeledPrice("Favor", price * 100)]

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
    update.message.reply_text("Thank you for your payment!")


def add_payment_handlers(dispatcher) -> None:
    dispatcher.add_handler(CommandHandler("payme", start_without_shipping_callback))

    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment_callback))

