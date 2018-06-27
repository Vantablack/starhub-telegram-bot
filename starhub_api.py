"""
Based on StarHub's mobile application (iOS v4.4.6) as at 21 June 2018
"""

import requests
import xmltodict


class StarHubApi:
    msso_login_url = 'https://login.starhubgee.com.sg/msso/mapp/api/login'
    fapi_login_url = 'https://fapi.starhub.com/MyStarhub/login/esso'
    fapi_all_usage_url = 'https://fapi.starhub.com/MyStarhub/usage?type=local'
    fapi_specific_usage_url = 'https://fapi.starhub.com/MyStarhub/usage/data/{phone_number}?type=LOCAL'
    user_agent_str = 'fe11e865d2af0b5978b4ecdd3d5441bc'
    x_sh_msa_version = '4.4.6'  # Corresponds to the StarHub's iOS app version

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

            return usage_dict
        else:
            print(r.status_code)
            print(r.text)

            return 'Unable to retrieve data usage'
