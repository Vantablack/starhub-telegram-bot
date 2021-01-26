"""
Based on StarHub's mobile application (iOS v5.1.15) as at 9 May 2020
"""
import logging
import requests


class StarHubApiException(Exception):
    """Raise this when there is an error with the StarHub API

    Args:
        http_code: HTTP Status Code associated with the error
        api_name: Name of the API causing this exception
        response_body: Response body of the request
        user_message: Custom message for the user/logger

    """

    def __init__(self, http_code, api_name, response_body, user_message=None):
        self.http_code = http_code
        self.api_name = api_name
        self.response_body = response_body
        self.user_message = user_message + 'HTTP Code: ' + self.http_code
        super().__init__(self.user_message)


class StarHubApi:
    """Represents StarHub API"""
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

    def get_user_token(self):
        """Retrieve user_token from MSSO login endpoint

        user_token will be cached as it will not expire
        This is tested on 8 December 2019

        Raises:
            StarHubApiError: Error associated with accessing StarHub's API
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

        res = requests.post(self.msso_login_url,
                            headers=headers,
                            json=mapp_body_dict,
                            timeout=10)

        if res.status_code == requests.codes.ok:
            res_json = res.json()
            self.user_token = res_json.get('user_token', None)
            return res_json.get('user_token', None)
        raise StarHubApiException(res.status_code, 'MSSO/MAPP/LOGIN',
                                  res.text, 'User token request failed')

    def get_utoken(self, user_token):
        """Retrieves u_token from the ESSO login endpoint

        If another u_token is generated, the previous one will be invalidated,
        causing a 401 Unauthorized error. To get around this issue,
        if 401 error code is encountered, function will reattempt request.

        Raises:
            StarHubApiError: Error associated with accessing StarHub's API
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

        res = requests.post(self.fapi_login_url,
                            headers=headers,
                            json=esso_body_dict,
                            timeout=10)
        if res.status_code == requests.codes.ok:
            res_json = res.json()
            self.u_token = res_json['userDetails']['utoken']
            return self.u_token
        if res.status_code != requests.codes.ok and \
                res.status_code == requests.codes.unauthorized:
            self.logger.warning(
                'Retrying get_utoken. Status code: %d', res.status_code)
            return self.get_utoken(self.get_user_token())
        raise StarHubApiException(res.status_code, 'FAPI/LOGIN/ESSO',
                                  res.text, 'UToken request failed')

    def get_phone_data_usage(self, utoken, phone_number):
        """Get a single phone number's data usage

        If another u_token is generated, the previous one will be invalidated,
        causing a 401 Unauthorized error. To get around this issue,
        if 401 error code is encountered, function will reattempt request.

        Raises:
            StarHubApiError: Error associated with accessing StarHub's API
        """

        headers = {
            'Authorization': utoken,
            'Accept': 'application/json',
            'User-Agent': self.user_agent_str,
            'x-sh-msa-version': self.x_sh_msa_version
        }
        res = requests.get(
            self.fapi_specific_usage_url.format(phone_number=phone_number),
            headers=headers,
            timeout=10)

        if res.status_code == requests.codes.ok:
            res_json = res.json()
            return res_json['mainContext']['present']['any'][0]['dataUsages']['usageDetail'][0]

        if res.status_code != requests.codes.ok \
                and res.status_code == requests.codes.unauthorized:
            self.logger.warning(
                'Retrying get_phone_data_usage. Status code: %d',
                res.status_code)
            utoken = self.get_utoken(self.get_user_token())
            return self.get_phone_data_usage(utoken, phone_number)

        raise StarHubApiException(res.status_code, 'FAPI/USAGE/DATA',
                                  res.text, 'Data usage request failed')
