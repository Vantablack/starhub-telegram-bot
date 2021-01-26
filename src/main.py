# !/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import textwrap
import sys
import tempfile

import arrow
from dateutil import rrule
from requests import RequestException
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Filters, CallbackQueryHandler
from matplotlib import pyplot as plt

from starhub_api import StarHubApi
from starhub_api import StarHubApiException

logging.basicConfig(
    format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('starhub_bot')

# Loading of config.json
with open('config/config.json', 'r') as f:
    config = json.load(f)

# Initializing StarHubApi using config.json
api = StarHubApi(user_id=config['user_id'],
                 user_password=config['user_password'])


def start_handler(update, context):
    text = ["*Here's a few commands that you can use:*"]
    for number in config['phone_numbers']:
        text.append("/usage {}".format(str(number)))
    update.message.reply_text('\n'.join(text), parse_mode='Markdown')


def usage_handler(update, context):
    """Callback function for 'usage' command"""
    args = context.args
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
                user_token = api.get_user_token()
                u_token = api.get_utoken(user_token)
                usage_dict = api.get_phone_data_usage(
                    u_token, phone_number=int(args[0]))

                formatted_str = format_usage_message(usage_dict)

                # Send selected data usage
                update.message.reply_text(
                    text=formatted_str, parse_mode='Markdown')
            except StarHubApiException as ex:
                logger.error(ex)
                update.message.reply_text(
                    text=str(ex.user_message), parse_mode='Markdown')
            except RequestException as ex:
                logger.error(ex)
                update.message.reply_text(text="Unexpected request exception")
            except:  # catch *all* exceptions
                ex = sys.exc_info()[0]
                logger.error(ex)
                update.message.reply_text(text="Unexpected request exception")


def history_handler(update, context):
    """Callback function for 'history' command"""
    args = context.args
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
                user_token = api.get_user_token()
                u_token = api.get_utoken(user_token)
                usage_dict = api.get_phone_data_usage(
                    u_token, phone_number=int(args[0]))

                formatted_str = format_usage_history_message(usage_dict)

                # Send bar chart
                generate_and_send_image_file(usage_dict, update)
                # Send selected data usage
                update.message.reply_text(
                    text=formatted_str, parse_mode='Markdown')
            except StarHubApiException as ex:
                logger.error(ex)
                update.message.reply_text(
                    text=str(ex.user_message), parse_mode='Markdown')
            except RequestException as ex:
                logger.error(ex)
                update.message.reply_text(text="Unexpected request exception")
            except:  # catch *all* exceptions
                ex = sys.exc_info()[0]
                logger.error(ex)
                update.message.reply_text(text="Unexpected request exception")


def callback_handler(update, context):
    """Callback function for CallbackQueryHandler"""
    query = update.callback_query

    # Show loading message
    query.edit_message_text(
        text='Please wait... ✋',
        parse_mode='Markdown')

    try:
        user_token = api.get_user_token()
        u_token = api.get_utoken(user_token)
        usage_dict = api.get_phone_data_usage(
            u_token, phone_number=query.data[2:])

        callback_type = query.data[:2]

        if callback_type == 'u-':
            formatted_str = format_usage_message(usage_dict)
        else:
            # Send bar chart
            generate_and_send_image_file(usage_dict, query)
            # Send selected data usage
            formatted_str = format_usage_history_message(usage_dict)

        # Send selected data usage
        query.message.reply_text(text=formatted_str, parse_mode='Markdown')
    except StarHubApiException as ex:
        logger.error(ex)
        query.message.reply_text(
            text=str(ex.user_message), parse_mode='Markdown')
    except RequestException as ex:
        logger.error(ex)
        update.message.reply_text(text="Unexpected request exception")
    except:  # catch *all* exceptions
        ex = sys.exc_info()[0]
        logger.error(ex)
        update.message.reply_text(text="Unexpected request exception")

    # Delete loading message
    query.message.delete()

    # Show inline keyboard again
    callback_type = query.data[:2]
    send_inline_keyboard(callback_type, query.message)


def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.error('Telegram error handler: "%s"', context.error)


def format_usage_message(usage_dict):
    daily_usage = usage_dict['dailyUsage']['day']
    usage_dict['C-todayUsage'] = daily_usage[-1]['usage']

    # Parsing last processed date time
    usage_dict['C-lastProcessedDateTime'] = datetime_json_to_arrow(usage_dict['lastProcessedDateTime']).format(
        'DD/MM/YYYY HH:mm:ss A')

    # Convert data units from GB/KB to MB (with 'N-' prefix)
    usage_dict = normalize_data_uom(usage_dict)

    # Adding analysis
    billing_start_date = datetime_json_to_arrow(usage_dict['fromDateTime'])
    billing_end_date = billing_start_date.shift(months=1)
    current_date = arrow.utcnow().to('Asia/Singapore')

    # Half closed interval [a,b)
    total_weekdays = num_weekdays(
        billing_start_date, billing_end_date.shift(days=-1))

    # Elapsed weekdays, Half closed interval [a,b)
    elapsed_weekdays = num_weekdays(
        billing_start_date, current_date.shift(days=-1))

    weekdays_left = total_weekdays - elapsed_weekdays

    # Get avg data per day (MB)
    # (total data left + data used today) / num of weekdays (inclusive of today)
    # only add the data used today if today is a weekday (weekday() not 5 or 6)
    if current_date.datetime.weekday() == 5 or current_date.datetime.weekday() == 6:
        avg_data_mb = float(
            (usage_dict['N-usageDifference'])) / (weekdays_left if (weekdays_left > 0) else 1)
    else:
        avg_data_mb = (float(usage_dict['N-usageDifference']) + float(usage_dict['C-todayUsage'])) / (
            weekdays_left if (weekdays_left > 0) else 1)

    usage_dict['C-avgData'] = avg_data_mb
    usage_dict['C-avgDataUOM'] = 'MB'
    usage_dict['C-weekdayLeft'] = weekdays_left

    usage_dict['C-progressBar'] = generate_progress_bar(float(usage_dict['N-totalUsage']),
                                                        float(
                                                            usage_dict['N-totalFreeUnits']),
                                                        suffix=str(
                                                            usage_dict['usagePercentage']) + '%',
                                                        length=20)

    # Markdown formatting for Telegram message formatting
    telegram_format_message = textwrap.dedent("""
        *Data Usage for {usageServiceId}*
        
        *{C-progressBar}*
        Total: *{totalFreeUnits} {totalFreeUnitsUOM}*
        Used: *{totalUsage} {totalUsageUOM}*
        Left: *{usageDifference} {differenceUOM}*
        Used Today: *{C-todayUsage} MB*
        
        *{C-weekdayLeft}* weekdays left (including today)
        
        Estimated limit per day:
        *{C-avgData:.2f} {C-avgDataUOM}*/day
        
        {C-lastProcessedDateTime}
        """.format(**usage_dict))

    return telegram_format_message


def format_usage_history_message(usage_dict):
    daily_usage = usage_dict['dailyUsage']['day']

    text = ['*Usage History (Day)*', '']

    for usage in daily_usage:
        date = datetime_json_to_arrow(usage['usageDate'])
        text.append(
            '{} - {} MB'.format(date.format('ddd DD/MM/YYYY'), str(usage['usage'])))
    return '\n'.join(text)


def generate_and_send_image_file(usage_dict, update):
    daily_usage = usage_dict['dailyUsage']['day']
    bar_heights = []
    bar_labels = []
    for usage in daily_usage:
        date = datetime_json_to_arrow(usage['usageDate'])
        if usage['totalVolumeUsageUOM'] == 'KB':
            # Convert KB to MB
            bar_heights.append(kb_to_mb(usage['totalVolumeUsage']))
        elif usage['totalVolumeUsageUOM'] == 'GB':
            # Convert GB to MB
            bar_heights.append(gb_to_mb(usage['totalVolumeUsage']))
        else:
            bar_heights.append(usage['totalVolumeUsage'])
        bar_labels.append(date.format('DD/MM'))

    plt.bar(range(len(bar_heights)), height=bar_heights)
    plt.xticks(range(len(bar_heights)), bar_labels, rotation=90)
    plt.title('Data Usage History {}'.format(usage_dict['usageServiceId']))

    with tempfile.TemporaryFile(suffix=".png") as tmpfile:
        # File position is at the end of the file.
        plt.savefig(tmpfile, format="png")
        tmpfile.seek(0)  # Rewind the file. (0: the beginning of the file)
        plt.clf()
        update.message.reply_photo(photo=tmpfile)


def send_inline_keyboard(callback_type, message):
    keyboard_btns = [[InlineKeyboardButton(str(number), callback_data=callback_type + str(number))] for number in
                     config['phone_numbers']]
    keyboard = keyboard_btns
    reply_markup = InlineKeyboardMarkup(keyboard)

    if callback_type == 'h-':
        message.reply_text(
            text='[Usage history] Please choose:', reply_markup=reply_markup)
    else:
        message.reply_text(
            text='[Current data usage] Please choose:', reply_markup=reply_markup)


def datetime_json_to_arrow(date_json):
    date_string = '{}/{}/{} {}:{}:{}'.format(
        date_json['day'],
        date_json['month'],
        date_json['year'],
        date_json['hour'],
        date_json['minute'],
        date_json['second'])
    return arrow.get(date_string, 'D/M/YYYY h:m:s')


# https://www.safaribooksonline.com/library/view/python-cookbook-2nd/0596007973/ch03s06.html
def num_weekdays(start, end):
    weekends = 5, 6  # saturdays and sundays/history
    weekdays = [x for x in range(7) if x not in weekends]
    days = rrule.rrule(rrule.DAILY, dtstart=start,
                       until=end, byweekday=weekdays)
    return days.count()


def normalize_data_uom(usage_dict):
    values_to_normalize = {
        'usage': 'uom',
        'freeUnits': 'freeUnitsUOM',
        'totalUsage': 'totalUsageUOM',
        'totalFreeUnits': 'totalFreeUnitsUOM',
        'usageDifference': 'differenceUOM',
        'dataShareUnits': 'dataShareUnitsUOM',
        'usageDataShare': 'usageDataShareUOM',
        'freeUsage': 'freeUsageUOM'
    }

    # Convert to MB
    for value in values_to_normalize:
        current_uom = usage_dict[values_to_normalize[value]]
        if (current_uom is not None) and (current_uom == 'KB'):
            # Convert KB to MB
            usage_dict['N-' + value] = kb_to_mb(usage_dict[value])
        elif (current_uom is not None) and (current_uom == 'GB'):
            # Convert GB to MB
            usage_dict['N-' + value] = gb_to_mb(usage_dict[value])
        elif (current_uom is not None):
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
    updater = Updater(config['telegram_token'], use_context=True)
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
        updater.bot.set_webhook(config.get(
            'webhook_url') + config.get('telegram_token'))
        logger.info('Bot started using webhook')
    else:
        updater.start_polling()
        logger.info('Bot started using long polling')

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
