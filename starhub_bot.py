# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import textwrap

import arrow
from collections import OrderedDict
from dateutil import rrule
from requests import RequestException
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, CallbackQueryHandler

from starhub_api import StarHubApi
from starhub_api import StarHubApiError

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Loading of config.json
with open('config/config.json', 'r') as f:
    config = json.load(f)

# Initializing StarHubApi using config.json
api = StarHubApi(user_id=config['user_id'], user_password=config['user_password'], logger=logger)


def start_handler(bot, update):
    text = ["*Here's a few commands that you can use:*"]
    for number in config['phone_numbers']:
        text.append("/usage {}".format(str(number)))
    update.message.reply_text('\n'.join(text), parse_mode='Markdown')


def usage_handler(bot, update, args):
    # Handle empty arguments
    if not args:
        callback_type = 'u-'
        send_inline_keyboard(callback_type, update.message)
    else:
        if int(args[0]) not in config['phone_numbers']:
            update.message.reply_text('Phone number is not recognized')
        else:
            try:
                # Send selected data usage
                user_token = api.get_user_token(retry = True)
                u_token = api.get_utoken(user_token, retry = True)
                usage_dict = api.get_phone_data_usage(u_token, phone_number=int(args[0]), retry = True)

                formatted_str = format_usage_message(usage_dict)

                # Send selected data usage
                update.message.reply_text(text=formatted_str, parse_mode='Markdown')
            except StarHubApiError as ex:
                logger.error(ex)
                # Send error message
                update.message.reply_text(text=str(ex.user_message), parse_mode='Markdown')
            except RequestException as ex:
                update.message.reply_text(text=str(ex), parse_mode='Markdown')


def history_handler(bot, update, args):
    # Handle empty arguments
    if not args:
        callback_type = 'h-'
        send_inline_keyboard(callback_type, update.message)
    else:
        if int(args[0]) not in config['phone_numbers']:
            update.message.reply_text('Phone number is not recognized')
        else:
            try:
                # Send selected data usage history
                user_token = api.get_user_token(retry = True)
                u_token = api.get_utoken(user_token, retry = True)
                usage_dict = api.get_phone_data_usage(u_token, phone_number=int(args[0]), retry = True)

                formatted_str = format_usage_history_message(usage_dict)

                # Send selected data usage
                update.message.reply_text(text=formatted_str, parse_mode='Markdown')
            except StarHubApiError as ex:
                logger.error(ex)
                # Send error message
                update.message.reply_text(text=str(ex.user_message), parse_mode='Markdown')
            except RequestException as ex:
                logger.error(ex)
                update.message.reply_text(text=str(ex), parse_mode='Markdown')


def callback_handler(bot, update):
    query = update.callback_query

    # Show loading message
    bot.edit_message_text(
        text='Please wait... ✋',
        parse_mode='Markdown',
        chat_id=query.message.chat_id,
        message_id=query.message.message_id)

    try:
        user_token = api.get_user_token(retry = True)
        u_token = api.get_utoken(user_token, retry = True)
        usage_dict = api.get_phone_data_usage(u_token, phone_number=query.data[2:], retry = True)

        callback_type = query.data[:2]

        if callback_type == 'u-':
            formatted_str = format_usage_message(usage_dict)
        else:
            formatted_str = format_usage_history_message(usage_dict)

        # Send selected data usage
        query.message.reply_text(text=formatted_str, parse_mode='Markdown')
    except StarHubApiError as ex:
        logger.error(ex)
        # Send error message
        query.message.reply_text(text=str(ex.user_message), parse_mode='Markdown')

    # Delete loading message
    bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

    # Show inline keyboard again
    callback_type = query.data[:2]
    send_inline_keyboard(callback_type, query.message)


def error_handler(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def format_usage_message(usage_dict):
    if len(usage_dict['DailyUsage']['Day']) > 0:
        if isinstance(usage_dict['DailyUsage']['Day'], OrderedDict):
            usage_dict['C-TodayUsage'] = usage_dict['DailyUsage']['Day']['Usage']
        else:
            usage_dict['C-TodayUsage'] = usage_dict['DailyUsage']['Day'][-1]['Usage']
    else:
        usage_dict['C-TodayUsage'] = str(0)

    # Parsing last processed date time
    usage_dict['C-LastProcessedDateTime'] = arrow.get(usage_dict['LastProcessedDateTime']).format(
        'DD/MM/YYYY HH:mm:ss A')

    # Convert data units from GB/KB to MB (with 'N-' prefix)
    normalize_data_uom(usage_dict)

    # Adding analysis
    billing_start_date = arrow.get(usage_dict['FromDateTime'])
    billing_end_date = billing_start_date.shift(months=1)
    current_date = arrow.utcnow().to('Asia/Singapore')

    # Half closed interval [a,b)
    total_weekdays = num_weekdays(billing_start_date, billing_end_date.replace(days=-1))

    # Elapsed weekdays, Half closed interval [a,b)
    elapsed_weekdays = num_weekdays(billing_start_date, current_date.replace(days=-1))

    weekdays_left = total_weekdays - elapsed_weekdays

    # Get avg data per day (MB)
    # (total data left + data used today) / num of weekdays (inclusive of today)
    # only add the data used today if today is a weekday (weekday() not 5 or 6)
    if current_date.datetime.weekday() == 5 or current_date.datetime.weekday() == 6:
        avg_data_mb = float((usage_dict['N-UsageDifference'])) / weekdays_left
    else:
        avg_data_mb = (float(usage_dict['N-UsageDifference']) + float(usage_dict['C-TodayUsage'])) / weekdays_left

    usage_dict['C-AvgData'] = avg_data_mb
    usage_dict['C-AvgDataUOM'] = 'MB'
    usage_dict['C-WeekdayLeft'] = weekdays_left

    usage_dict['C-ProgressBar'] = generate_progress_bar(float(usage_dict['N-TotalUsage']),
                                                        float(usage_dict['N-TotalFreeUnits']),
                                                        suffix=str(usage_dict['UsagePercentage']) + '%',
                                                        length=20)

    # Markdown formatting for Telegram message formatting
    telegram_format_message = textwrap.dedent("""
        *Data Usage for {UsageServiceId}*
        
        *{C-ProgressBar}*
        Total: *{TotalFreeUnits} {TotalFreeUnitsUOM}*
        Used: *{TotalUsage} {TotalUsageUOM}*
        Left: *{UsageDifference} {DifferenceUOM}*
        Used Today: *{C-TodayUsage} MB*
        
        *{C-WeekdayLeft}* weekdays left (including today)
        
        Average data usage per day:
        *{C-AvgData:.2f} {C-AvgDataUOM}*/day
        
        {C-LastProcessedDateTime}
        """.format(**usage_dict))

    return telegram_format_message


def format_usage_history_message(usage_dict):
    daily_usage = usage_dict['DailyUsage']['Day']

    text = ['*Usage History (Day)*', '']

    for usage in daily_usage:
        date = arrow.get(usage['UsageDate'])
        text.append(
            '{} - {} MB'.format(date.format('ddd DD/MM/YYYY'), str(usage['Usage'])))
    return '\n'.join(text)


def send_inline_keyboard(callback_type, message):
    keyboard_btns = [[InlineKeyboardButton(str(number), callback_data=callback_type + str(number))] for number in
                     config['phone_numbers']]
    keyboard = keyboard_btns
    reply_markup = InlineKeyboardMarkup(keyboard)

    if callback_type == 'h-':
        message.reply_text(text='[Usage history] Please choose:', reply_markup=reply_markup)
    else:
        message.reply_text(text='[Current data usage] Please choose:', reply_markup=reply_markup)


# https://www.safaribooksonline.com/library/view/python-cookbook-2nd/0596007973/ch03s06.html
def num_weekdays(start, end):
    weekends = 5, 6  # saturdays and sundays/history
    weekdays = [x for x in range(7) if x not in weekends]
    days = rrule.rrule(rrule.DAILY, dtstart=start, until=end, byweekday=weekdays)
    return days.count()


def normalize_data_uom(usage_dict):
    values_to_normalize = {
        'Usage': 'UOM',
        'FreeUnits': 'FreeUnitsUOM',
        'TotalUsage': 'TotalUsageUOM',
        'TotalFreeUnits': 'TotalFreeUnitsUOM',
        'UsageDifference': 'DifferenceUOM',
        'DataShareUnits': 'DataShareUnitsUOM',
        'UsageDataShare': 'UsageDataShareUOM',
        'FreeUsage': 'FreeUsageUOM'
    }

    # Convert to MB
    for value in values_to_normalize:
        if usage_dict.get(values_to_normalize[value], False) and usage_dict[values_to_normalize[value]] == 'KB':
            # Convert KB to MB
            usage_dict['N-' + value] = kb_to_mb(usage_dict[value])
        elif usage_dict.get(values_to_normalize[value], False) and usage_dict[values_to_normalize[value]] == 'GB':
            # Convert GB to MB
            usage_dict['N-' + value] = gb_to_mb(usage_dict[value])
        elif usage_dict.get(values_to_normalize[value], False):
            usage_dict['N-' + value] = usage_dict[value]

    return usage_dict


# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def generate_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    # percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    return '%s |%s| %s' % (prefix, bar, suffix)
    # return '\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix)


def gb_to_mb(gb_data):
    return 1024 * float(gb_data)


def kb_to_mb(kb_data):
    return (1. / 1024) * float(kb_data)


def mb_to_gb(mb_data):
    return float(mb_data) / 1024


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(config['telegram_token'])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        CommandHandler('start', start_handler,
                       filters=Filters.user(config['whitelisted_user_names'])))
    dispatcher.add_handler(
        CommandHandler('usage', usage_handler,
                       pass_args=True,
                       filters=Filters.user(config['whitelisted_user_names'])))
    dispatcher.add_handler(
        CommandHandler('history', history_handler,
                       pass_args=True,
                       filters=Filters.user(config['whitelisted_user_names'])))
    dispatcher.add_handler(CallbackQueryHandler(callback_handler))
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    if config.get('webhook_url', None):
        updater.start_webhook(listen="",
                              port=80,
                              url_path=config.get('telegram_token'))
        updater.bot.set_webhook(config.get('webhook_url') + config.get('telegram_token'))
        logger.info('Bot started using webhook')
    else:
        updater.start_polling()
        logger.info('Bot started using long polling')

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
