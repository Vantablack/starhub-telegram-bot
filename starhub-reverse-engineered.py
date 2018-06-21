import requests, http.cookies, xml.etree.cElementTree as ET
from xml.etree.ElementTree import tostring

"""
TODO:

1) Specify number to retrieve
 
"""

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
        'User-Agent': 'fe11e865d2af0b5978b4ecdd3d5441bc',
        'Connection': 'keep-alive'
    }

    r = requests.post(msso_login_url, headers=headers, json=mapp_body_dict)
    if r.status_code == 200:
        res_json = r.json()
        print('user_token: ' + res_json['user_token'])
        getutoken(res_json['user_token'])


def getutoken(user_token):
    headers = {
        'User-Agent': 'fe11e865d2af0b5978b4ecdd3d5441bc',
        'Content-Type': 'text/xml'
    }

    logins = ET.Element("Logins")
    logins.attrib['xmlns'] = 'http://www.starhub.com/FAPI_Logins'
    esso_login = ET.SubElement(logins, "ESSOLogin")
    ET.SubElement(esso_login, "vctk3").text = user_token
    ET.SubElement(esso_login, "LoginId").text = user_id
    ET.SubElement(esso_login, "SiteId").text = 'mystarhub'
    ET.SubElement(esso_login, "SiteKey").text = '1q23TypKwgba7984'

    r = requests.post(fapi_login_url, headers=headers, data=tostring(logins).decode('utf-8'))
    if r.status_code == 200:

        # Retrieve cookie value
        c = http.cookies.SimpleCookie()
        c.load(r.headers['Set-Cookie'])
        print('Cookie: ' + c['starhub.com'].value)

        root = ET.ElementTree(ET.fromstring(r.text))
        print('UToken: ' + root.getroot()[0][2].text)

        getusage(utoken=root.getroot()[0][2].text, cookie_value=c['starhub.com'].value)
    else:
        print(r.status_code)
        print(r.text)


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


getusertoken()
