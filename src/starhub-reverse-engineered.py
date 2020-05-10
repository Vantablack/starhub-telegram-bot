import requests

msso_login_url = 'https://login.starhubgee.com.sg/msso/mapp/api/login'
fapi_login_url = 'https://fapi.starhub.com/MyStarhub/login/esso'
fapi_usage_url = 'https://fapi.starhub.com/MyStarhub/usage?type=local'

user_id = 'PLAINTEXT_GMAIL'
user_password = 'ENCRYPTED_PASSWORD'


def getusertoken():
    mapp_body_dict = {
        'site_id': 'mystarhub',
        'user_id': user_id,
        'user_password': user_password
    }

    headers = {
        'User-Agent': '870330a7f6fe26b489e0f353753504ad',
        'Accept': 'application/json'
    }

    r = requests.post(
        msso_login_url,
        headers=headers,
        json=mapp_body_dict)

    if r.status_code == requests.codes.ok:
        res_json = r.json()
        print('user_token: ' + res_json.get('user_token', None))
        # getutoken(res_json['user_token'])
        return res_json.get('user_token', None)


def getutoken(user_id, user_token):
    headers = {
        'User-Agent': '870330a7f6fe26b489e0f353753504ad',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-sh-msa-version': '5.1.15'
    }

    esso_body_dict = {
        'essoLogin': {
            "loginId": user_id,
            "siteId": "mystarhub",
            "siteKey": "1q23TypKwgba7984",
            "vctk3": user_token
        }
    }

    r = requests.post(fapi_login_url,
                        headers=headers,
                        json=esso_body_dict,
                        timeout=10)

    if r.status_code == requests.codes.ok:
        res_json = r.json()
        print('utoken: ' + res_json['userDetails']['utoken'])
        return res_json['userDetails']['utoken']
    else:
        print('utoken failed: ' + r.status_code)
        
    #     # Retrieve cookie value
    #     c = http.cookies.SimpleCookie()
    #     c.load(r.headers['Set-Cookie'])
    #     print('Cookie: ' + c['starhub.com'].value)

    #     root = ET.ElementTree(ET.fromstring(r.text))
    #     print('UToken: ' + root.getroot()[0][2].text)

    #     getusage(utoken=root.getroot()[0][2].text, cookie_value=c['starhub.com'].value)
    # else:
    #     print(r.status_code)
    #     print(r.text)


def getusage(utoken, cookie_value):
    headers = {
        'User-Agent': 'fe11e865d2af0b5978b4ecdd3d5441bc',
        'Authorization': utoken,
        'x-sh-msa-version': '4.4.5'
    }

    cookie = {
        'starhub.com': cookie_value
    }

    r = requests.get(fapi_usage_url, headers=headers, cookies=cookie)
    if r.status_code == 200:
        print(r.text)

        usage_namespace = {'ns10': 'http://www.starhub.com/FAPI_Usage'}

        root = ET.ElementTree(ET.fromstring(r.text)).getroot()
        for elem in root.find('.//ns10:UsageDetail[ns10:UsageServiceId="12345678"]', namespaces=usage_namespace):
            print(elem.tag + ': ' + elem.text)
        # root = ET.ElementTree(ET.fromstring(r.text))
    else:
        print(r.status_code)
        print(r.text)


user_token = getusertoken(user_id, user_password)
u_token = getutoken(user_id, user_token)