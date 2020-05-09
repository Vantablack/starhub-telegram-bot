"""
Based on StarHub's mobile application (iOS v5.1.15) as at 9 May 2020
"""
import textwrap
import uuid
import logging

import arrow
import requests


class StarHubApiError(ValueError):
    """Raise this when there is an error with the StarHub API"""

    def __init__(self, message, user_message=None):
        # Call the base class constructor with the parameters it needs (Python 3+)
        super().__init__(message)
        self.user_message = user_message


class StarHubApi:
    msso_login_url = 'https://login.starhubgee.com.sg/msso/mapp/api/login'
    fapi_login_url = 'https://fapi.starhub.com/MyStarhub/login/esso'
    fapi_all_usage_url = 'https://fapi.starhub.com/MyStarhub/usage?type=local'
    fapi_specific_usage_url = 'https://fapi.starhub.com/MyStarhub/usage/data/{phone_number}?usageOption=LOCAL'
    user_agent_str = '870330a7f6fe26b489e0f353753504ad'
    x_sh_msa_version = '5.1.15'  # Corresponds to the StarHub's iOS app version

    def __init__(self, user_id, user_password):
        self.logger = logging.getLogger('starhub_api')
        self.user_id = user_id
        self.user_password = user_password
        self.user_token = None
        self.u_token = None

    def get_user_token(self, retry=False):
        """Retrieve user_token from MSSO login endpoint

        Note:
            Will cache the user_token as it will not expire (tested: 8 December 2019)
        """
        if self.user_token:
            return self.user_token

        mapp_body_dict = {
            'site_id': 'mystarhub',
            'user_id': self.user_id,
            'user_password': self.user_password
        }

        headers = {
            'User-Agent': self.user_agent_str,
            'Accept': 'application/json'
        }

        r = requests.post(self.msso_login_url,
                          headers=headers,
                          json=mapp_body_dict,
                          timeout=10)

        if r.status_code == requests.codes.ok:
            res_json = r.json()
            self.user_token = res_json.get('user_token', None)
            return res_json.get('user_token', None)
        elif r.status_code != requests.codes.ok and retry == True:
            self.logger.warning('Retrying get_user_token. Status code: %d', r.status_code)
            return self.get_user_token(retry=False)
        else:
            time = arrow.utcnow().to('Asia/Singapore').format('DD-MM-YYYY HH:mm A')
            ref_code = time + '-' + str(uuid.uuid4()).split('-')[0]

            raise StarHubApiError(message=textwrap.dedent("""
            *REF: {0}*
            *MSSO/MAPP/LOGIN*
            
            User token request failed
            
            Request response code: {1}
            
            Response body:
            ```{2}```
            """.format(ref_code, r.status_code, r.text)),
                                  user_message='*Errored. Reference code:* `{0}`'.format(ref_code))

    def get_utoken(self, user_token, retry=False):
        """Retrieves u_token from the ESSO login endpoint

        Note:
            If another u_token is generated, the previous one will be invalidated,
            causing a 401 Unauthorized error if used
        """

        headers = {
            'User-Agent': self.user_agent_str,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-sh-msa-version': self.x_sh_msa_version
        }

        esso_body_dict = {
            'essoLogin': {
                "loginId": self.user_id,
                "siteId": "mystarhub",
                "siteKey": "1q23TypKwgba7984",
                "vctk3": user_token
            }
        }

        r = requests.post(self.fapi_login_url,
                          headers=headers,
                          json=esso_body_dict,
                          timeout=10)
        if r.status_code == requests.codes.ok:
            res_json = r.json()
            self.u_token = res_json['userDetails']['utoken']
            return self.u_token
        elif r.status_code != requests.codes.ok and retry == True:
            self.logger.warning('Retrying get_utoken. Status code: %d', r.status_code)
            user_token = self.get_user_token()
            return self.get_utoken(user_token, retry=False)
        else:
            time = arrow.utcnow().to('Asia/Singapore').format('DD-MM-YYYY HH:mm A')
            ref_code = time + '-' + str(uuid.uuid4()).split('-')[0]

            raise StarHubApiError(message=textwrap.dedent("""
            *REF: {0}*
            *FAPI/LOGIN/ESSO*
            
            UToken request failed
            
            Request response code: {1}
            
            Response body:
            ```{2}```
            """.format(ref_code, r.status_code, r.text)),
                                  user_message='*Errored. Reference code:* `{0}`'.format(ref_code))

    def get_phone_data_usage(self, utoken, phone_number, retry=False):
        """Get a single phone number's data usage"""

        headers = {
            'Authorization': utoken,
            'Accept': 'application/json',
            'User-Agent': self.user_agent_str,
            'x-sh-msa-version': self.x_sh_msa_version
        }
        r = requests.get(self.fapi_specific_usage_url.format(phone_number=phone_number),
                         headers=headers,
                         timeout=10)

        if r.status_code == requests.codes.ok:
            res_json = r.json()
            return res_json['mainContext']['present']['any'][0]['dataUsages']['usageDetail'][0]
        elif r.status_code != requests.codes.ok and retry == True:
            self.logger.warning('Retrying get_phone_data_usage. Status code: %d', r.status_code)
            utoken = self.get_utoken(self.get_user_token())
            return self.get_phone_data_usage(utoken, phone_number, retry=False)
        else:
            time = arrow.utcnow().to('Asia/Singapore').format('DD-MM-YYYY HH:mm A')
            ref_code = time + '-' + str(uuid.uuid4()).split('-')[0]

            raise StarHubApiError(message=textwrap.dedent("""
            *REF: {0}*
            *FAPI/USAGE/DATA*
            
            Data usage request failed
            
            Request response code: {1}
            
            Response body:
            ```{2}```
            """.format(ref_code, r.status_code, r.text)),
                                  user_message='*Errored. Reference code:* `{0}`'.format(ref_code))
