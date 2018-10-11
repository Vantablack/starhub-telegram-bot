# StarHub Application Endpoints

## Tools

[mitmproxy (mitmweb)](https://mitmproxy.org/) was used to capture and inspect the network requests made by the mobile application

Guide for setting up mitmproxy with an iOS device: https://jasdev.me/intercepting-ios-traffic

> Note: For iOS devices, an additional step is required: https://docs.mitmproxy.org/stable/concepts-certificates/#installing-the-mitmproxy-ca-certificate-manually

## Authentication Endpoints

After some trial and errors the authentication flow is structured as such:

1) https://login.starhubgee.com.sg/msso/mapp/api/login (a.k.a MSSO)
    - Retrieve `user_token` from response (see MSSO Login reference)
    - Even though the payload contains a `expiry` field, it seems like the `user_token` can still be used even after it is _expired_
2) https://fapi.starhub.com/MyStarhub/login/esso (a.k.a ESSO)
    - Using `user_token` retrieve `UToken` from response (see ESSO Login reference)

## Data Endpoints

The `UToken` retrieved from the authentication will be used for all the requests here.

*  **Headers**

   'User-Agent': 'fe11e865d2af0b5978b4ecdd3d5441bc'
   'Authorization': $UTOKEN,
   'x-sh-msa-version': '4.4.6'


Endpoints:

- https://fapi.starhub.com/MyStarhub/usage?type=local
    - Retrieve all usage (SMS/Voice/Data) for all numbers
- https://fapi.starhub.com/MyStarhub/usage/data/{phone_number}?type=LOCAL
    - Retrieve data usage for a `phone_number`

## Endpoint Reference

### MSSO Login

* **URL**

  https://login.starhubgee.com.sg/msso/mapp/api/login

* **Method:**

  `POST`
  
*  **Headers**

   'User-Agent': 'fe11e865d2af0b5978b4ecdd3d5441bc'

* **Data Params**

  JSON

    ```json
    {
      "site_id": "mystarhub",
      "user_id": "---REDACTED---@yourmail.com",
      "user_password": "---REDACTED---"
    }
    ```

* **Success Response:**

  * **Code:** 200 <br />
    **Content:** JSON

    ```json
    {
        "expiry": 1529138910047,
        "ret_code": 1000,
        "ret_msg": "Success",
        "session_id": "---REDACTED---",
        "sso_token": "---REDACTED---",
        "time_issued": 1529137110047,
        "user_data": {
            "dob": "---REDACTED---",
            "email": "---REDACTED---@yourmail.com",
            "gender": "---REDACTED---",
            "name": "---REDACTED---",
            "nick_name": "null",
            "status": "bill_associated",
            "uuid": "---REDACTED---@yourmail.com"
        },
        "user_id": "---REDACTED---@yourmail.com",
        "user_token": "---REDACTED---"
    }
    ```
    
### ESSO Login

* **URL**

  https://fapi.starhub.com/MyStarhub/login/esso

* **Method:**

  `POST`
  
*  **Headers**
  
  'User-Agent': 'fe11e865d2af0b5978b4ecdd3d5441bc'

* **Data Params**

  XML

    ```xml
    <Logins xmlns="http://www.starhub.com/FAPI_Logins">
      <ESSOLogin>
        <vctk3>---REDACTED---</vctk3>
        <LoginId>---REDACTED---@yourmail.com</LoginId>
        <SiteId>mystarhub</SiteId>
        <SiteKey>1q23TypKwgba7984</SiteKey>
      </ESSOLogin>
    </Logins>
    ```

* **Success Response:**

  * **Code:** 200 <br />
    **Content:** XML

    ```xml
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <IR IRID="IR00057">
      <UserDetails>
        <UID>---REDACTED---@gmail.com</UID>
        <UType>HUBID</UType>
        <UToken>---REDACTED---</UToken>
        <LastLogin>2018-06-16T16:20:10.000</LastLogin>
        <Prepaid>false</Prepaid>
      </UserDetails>
      ...
    </IR>
    ```