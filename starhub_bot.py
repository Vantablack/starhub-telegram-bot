# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, CallbackQueryHandler

from starhub_api import StarHubApi

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Loading of config.json
with open('config/config.json', 'r') as f:
    config = json.load(f)

# Initializing StarHubApi using config.json
api = StarHubApi(user_id=config['user_id'], user_password=config['user_password'])


def start(bot, update):
    text = ["*Here's a few commands that you can use:*"]
    for number in config['phone_numbers']:
        text.append("/data {}".format(str(number)))
    update.message.reply_text('\n'.join(text), parse_mode='Markdown')


def data(bot, update, args):
    # Handle empty arguments
    if not args:
        keyboard_btns = [[InlineKeyboardButton(str(number), callback_data=str(number))] for number in
                         config['phone_numbers']]
        keyboard = keyboard_btns
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('Please choose:', reply_markup=reply_markup)
    else:
        if int(args[0]) not in config['phone_numbers']:
            update.message.reply_text('Phone number is not recognized')
        else:
            # Send selected data usage
            update.message.reply_text(
                text=api.get_phone_data_usage(utoken=api.get_utoken(api.get_user_token()), phone_number=int(args[0])),
                parse_mode='Markdown')


def button(bot, update):
    query = update.callback_query

    # Show loading message
    bot.edit_message_text(
        text='Please wait... ✋',
        parse_mode='Markdown',
        chat_id=query.message.chat_id,
        message_id=query.message.message_id)

    # Send selected data usage
    bot.send_message(
        text=api.get_phone_data_usage(utoken=api.get_utoken(api.get_user_token()), phone_number=query.data),
        parse_mode='Markdown',
        chat_id=query.message.chat_id,
        message_id=query.message.message_id)

    # Delete loading message
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

    # Show inline keyboard again
    keyboard_btns = [[InlineKeyboardButton(str(number), callback_data=str(number))] for number in
                     config['phone_numbers']]
    keyboard = keyboard_btns
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=query.message.chat_id, text='Please choose:', reply_markup=reply_markup)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['telegram_token'])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        CommandHandler('start', start, filters=Filters.user(config['whitelisted_user_names'])))
    dispatcher.add_handler(
        CommandHandler('data', data, pass_args=True, filters=Filters.user(config['whitelisted_user_names'])))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    print('Bot started using long polling')

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
