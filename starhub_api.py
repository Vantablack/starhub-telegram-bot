"""
Based on StarHub's mobile application (iOS v4.4.6) as at 21 June 2018
"""
import textwrap

import requests
import xmltodict


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


def normalize_data_uom(usage_dict):
    defs = {'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}

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
        if usage_dict[value] == 'KB':
            # Convert KB to MB
            megabyte = 1. / 1024
            usage_dict[value] = megabyte * float(usage_dict[value])
            usage_dict[values_to_normalize[value]] = 'MB'
        elif usage_dict[values_to_normalize[value]] == 'GB':
            # Convert GB to MB
            gigabyte = 1024
            usage_dict[value] = gigabyte * float(usage_dict[value])
            usage_dict[values_to_normalize[value]] = 'MB'

        # usage_dict[value] = float(usage_dict[value]) * defs[usage_dict[values_to_normalize[value]]]

    # for i in usage_dict:
    #     print(i + ': ' + usage_dict[i])

    return usage_dict


class StarHubApi:
    msso_login_url = 'https://login.starhubgee.com.sg/msso/mapp/api/login'
    fapi_login_url = 'https://fapi.starhub.com/MyStarhub/login/esso'
    fapi_all_usage_url = 'https://fapi.starhub.com/MyStarhub/usage?type=local'
    fapi_specific_usage_url = 'https://fapi.starhub.com/MyStarhub/usage/data/{phone_number}?type=LOCAL'
    user_agent_str = 'fe11e865d2af0b5978b4ecdd3d5441bc'
    x_sh_msa_version = '4.4.6'  # theoretically this should correspond to the StarHub's iOS app version

    def __init__(self, user_id, user_password):
        self.user_id = user_id
        self.user_password = user_password

    def get_user_token(self):
        mapp_body_dict = {
            'site_id': 'mystarhub',
            'user_id': self.user_id,
            'user_password': self.user_password
        }

        headers = {
            'User-Agent': self.user_agent_str
        }

        r = requests.post(self.msso_login_url, headers=headers, json=mapp_body_dict)
        if r.status_code == 200:
            res_json = r.json()
            print('user_token: ' + res_json['user_token'])
            return res_json['user_token']

    def get_utoken(self, user_token):
        headers = {
            'User-Agent': self.user_agent_str,
            'Content-Type': 'text/xml'
        }

        request_xml_dict = {
            'Logins': {
                '@xmlns': 'http://www.starhub.com/FAPI_Logins',
                'ESSOLogin': {
                    'vctk3': user_token,
                    'LoginId': self.user_id,
                    'SiteId': 'mystarhub',
                    'SiteKey': '1q23TypKwgba7984'
                }
            }
        }

        r = requests.post(self.fapi_login_url,
                          headers=headers,
                          data=xmltodict.unparse(request_xml_dict))
        if r.status_code == 200:

            token_response = xmltodict.parse(r.text, process_namespaces=True, namespaces={
                'http://www.starhub.com/FrontAPI': None
            })

            return token_response['IR']['UserDetails']['UToken']
        else:
            print(r.status_code)
            print(r.text)

    def get_phone_data_usage(self, utoken, phone_number):
        headers = {
            'Authorization': utoken,
            'User-Agent': self.user_agent_str,
            'x-sh-msa-version': self.x_sh_msa_version
        }

        r = requests.get(self.fapi_specific_usage_url.format(phone_number=phone_number), headers=headers)
        if r.status_code == 200:
            # Transform XML to dict
            # see https://github.com/martinblech/xmltodict
            usage_dict = xmltodict.parse(r.text, process_namespaces=True, namespaces={
                'http://www.starhub.com/FrontAPI': None,
                'http://www.starhub.com/FAPI_Usage': None
            })
            usage_dict = usage_dict['IR']['MainContext']['Present']['UsageList']['DataUsages']['UsageDetail']

            # usage_dict = normalize_dataUOM(usage_dict)
            # normalize_dataUOM(usage_dict)

            # TODO: Add progress bar
            # Currently broken as total usage could be KB/MB/GB while TotalFreeUnits could be KB/MB/GB
            # usage_dict['ProgressBar'] = generate_progress_bar(float(usage_dict['TotalUsage']),
            #                                                   float(usage_dict['TotalFreeUnits']),
            #                                                   length=20)

            usage_dict['C-TodayUsage'] = usage_dict['DailyUsage']['Day'][-1]['Usage']

            # Markdown formatting for Telegram message formatting
            telegram_format_message = textwrap.dedent("""
                    *Data Usage for {UsageServiceId}*

                    *{TotalUsage} {TotalUsageUOM}* of *{TotalFreeUnits} {TotalFreeUnitsUOM}* used

                    *{UsageDifference} {DifferenceUOM}* left
                    
                    *{C-TodayUsage} MB* used today
                    """.format(**usage_dict))

            return telegram_format_message
        else:
            print(r.status_code)
            print(r.text)

            return 'Unable to retrieve data usage'
