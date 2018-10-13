"""
Based on StarHub's mobile application (iOS v4.6.0) as at 14 October 2018
"""
import textwrap
import uuid

import arrow
import requests
import xmltodict

class StarHubApiError(ValueError):
    """Raise this when there is an error with the StarHub API"""
    def __init__(self, message, user_message = None):
        # Call the base class constructor with the parameters it needs (Python 3+)
        super().__init__(message)
        self.user_message = user_message

class StarHubApi:
    msso_login_url = 'https://login.starhubgee.com.sg/msso/mapp/api/login'
    fapi_login_url = 'https://fapi.starhub.com/MyStarhub/login/esso'
    fapi_all_usage_url = 'https://fapi.starhub.com/MyStarhub/usage?type=local'
    fapi_specific_usage_url = 'https://fapi.starhub.com/MyStarhub/usage/data/{phone_number}?type=LOCAL'
    user_agent_str = 'fe11e865d2af0b5978b4ecdd3d5441bc'
    x_sh_msa_version = '4.6.0'  # Corresponds to the StarHub's iOS app version

    def __init__(self, user_id, user_password, logger):
        self.logger = logger
        self.user_id = user_id
        self.user_password = user_password
        self.user_token = None
        self.u_token = None

    def get_user_token(self, retry = False):
        """Retrieve user_token from MSSO login endpoint

        Note:
            Will cache the user_token as it will not expire (tested: 11 October 2018)
        """
        if self.user_token:
            return self.user_token

        mapp_body_dict = {
            'site_id': 'mystarhub',
            'user_id': self.user_id,
            'user_password': self.user_password
        }

        headers = {
            'User-Agent': self.user_agent_str
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
            logger.warn('Retrying get_user_token. Status code:{0}', r.status_code)
            return self.get_user_token(retry = False)
        else:
            time = arrow.utcnow().to('Asia/Singapore').format('DD-MM-YYYY HH:mm A')
            ref_code = time + '-' + str(uuid.uuid4()).split('-')[0]

            raise StarHubApiError(message = textwrap.dedent("""
            *REF: {0}*
            *MSSO/MAPP/LOGIN*
            
            User token request failed
            
            Request response code: {1}
            
            Response body:
            ```{2}```
            """.format(ref_code, r.status_code, r.text)),
            user_message = '*Errored. Reference code:* `{0}`'.format(ref_code))

    def get_utoken(self, user_token, retry = False):
        """Retrieves u_token from the ESSO login endpoint

        Note:
            If another u_token is generated, the previous one will be invalidated,
            causing a 401 Unauthorized error if used
        """

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
                          data=xmltodict.unparse(request_xml_dict),
                          timeout=10)
        if r.status_code == requests.codes.ok:
            token_response = xmltodict.parse(r.text, process_namespaces=True, namespaces={
                'http://www.starhub.com/FrontAPI': None
            })
            self.u_token = token_response['IR']['UserDetails']['UToken']
            return self.u_token
        elif r.status_code != requests.codes.ok and retry == True:
            logger.warn('Retrying get_utoken. Status code:{0}', r.status_code)
            user_token = self.get_user_token();
            return self.get_utoken(user_token, retry = False)
        else:
            time = arrow.utcnow().to('Asia/Singapore').format('DD-MM-YYYY HH:mm A')
            ref_code = time + '-' + str(uuid.uuid4()).split('-')[0]

            raise StarHubApiError(message = textwrap.dedent("""
            *REF: {0}*
            *FAPI/LOGIN/ESSO*
            
            UToken request failed
            
            Request response code: {1}
            
            Response body:
            ```{2}```
            """.format(ref_code, r.status_code, r.text)),
            user_message = '*Errored. Reference code:* `{0}`'.format(ref_code))

    def get_phone_data_usage(self, utoken, phone_number, retry = False):
        """Get a single phone number's data usage
        """

        headers = {
            'Authorization': utoken,
            'User-Agent': self.user_agent_str,
            'x-sh-msa-version': self.x_sh_msa_version
        }

        r = requests.get(self.fapi_specific_usage_url.format(phone_number=phone_number),
                        headers=headers,
                        timeout=10)

        if r.status_code == requests.codes.ok:
            # Transform XML to dict
            # see https://github.com/martinblech/xmltodict
            usage_dict = xmltodict.parse(r.text, process_namespaces=True, namespaces={
                'http://www.starhub.com/FrontAPI': None,
                'http://www.starhub.com/FAPI_Usage': None
            })
            usage_dict = usage_dict['IR']['MainContext']['Present']['UsageList']['DataUsages']['UsageDetail']
            return usage_dict
        elif r.status_code != requests.codes.ok and retry == True:
            logger.warn('Retrying get_phone_data_usage. Status code:{0}', r.status_code)
            utoken = self.get_utoken(self.get_user_token())
            return self.get_phone_data_usage(utoken, phone_number, retry = False)
        else:
            time = arrow.utcnow().to('Asia/Singapore').format('DD-MM-YYYY HH:mm A')
            ref_code = time + '-' + str(uuid.uuid4()).split('-')[0]

            raise StarHubApiError(message = textwrap.dedent("""
            *REF: {0}*
            *FAPI/USAGE/DATA*
            
            Data usage request failed
            
            Request response code: {1}
            
            Response body:
            ```{2}```
            """.format(ref_code, r.status_code, r.text)),
            user_message = '*Errored. Reference code:* `{0}`'.format(ref_code))