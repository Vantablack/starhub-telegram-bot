# StarHub v5.1.5 2019 Update

In December 2019, the authentication requests stopped working and was receiving HTTP Status `202` with the message
`Please kindly download the latest My StarHub App.`

My initial suspicion was that StarHub has changed the way their authentication methods worked, so I used the
following tools to understand what was changed:
- [mitmproxy](https://mitmproxy.org/)
- [\[GitHub\] skylot/jadx](https://github.com/skylot/jadx) to decompile
[My StarHub](https://play.google.com/store/apps/details?id=com.starhub.csselfhelp&hl=en_US) app

What I found out was: **not much has changed**.

## Inspecting HTTP Requests

### Authentication Endpoint
Authentication is largely the same, a request will be made to 
`https://login.starhubgee.com.sg/msso/mapp/api/login` (MSSO) first then followed by a request to
`https://fapi.starhub.com/MyStarhub/login/esso`  (ESSO). The finally a token is retrieved to authenticate.

**Only ESSO is updated.**

Previous HTTP inspection revealed that the request body to ESSO was made in XML, however, it is now done in JSON.

```json
{
    "essoLogin": {
        "loginId": "your@email.com",
        "siteId": "mystarhub",
        "siteKey": "1q23TypKwgba7984",
        "vctk3": "r@nd0m_token"
    }
}
```

Another change is the HTTP `User-Agent` field is updated from `fe11e865d2af0b5978b4ecdd3d5441bc` to `870330a7f6fe26b489e0f353753504ad`

This is probably how StarHub determine the version of the app?

### Data Usage Endpoint

As for the data usage endpoint, two discovery were made:
- using `Accept: application/json` will force the server to return JSON instead of XML (easier to parse)
- the query param `usageOption` will yield different results
    - LOCAL: will return data usage with daily usage
    - DAILY: will only return daily usage

## Summary

After updating the ESSO endpoint changes, making the server return JSON and adapting the code for the new changes,
the bot works again.

## Extras

- [Reverse engineering and penetration testing on Android apps: my own list of tools](https://www.andreafortuna.org/2019/07/18/reverse-engineering-and-penetration-testing-on-android-apps-my-own-list-of-tools/)
- [Reversing HackEx - An android game](http://web.archive.org/web/20191114195615/https://0x00sec.org/t/reversing-hackex-an-android-game/16243)

When decompiling the APK, the resulting sourcecode was harder to navigate because it was more obfuscated as compared
to the older version.

Tips on how to find out where the encryption happens:
- search for a few keywords such as `encrypt` or `password`
- find out what is the main Activity (screen) or Fragment
- use runtime inspection tools such as Frida to hook on to

Here are some interesting files that I used to determine that the encryption methods was not changed

```java
package com.starhub.newmsa.utils;

import org.springframework.security.crypto.encrypt.Encryptors;

/* renamed from: com.starhub.newmsa.utils.a */
/* compiled from: AES.kt */
public final class C3513a {
    /* ... */

    /* renamed from: c */
    public final String mo21552c(String str) {
        C0889i.m2284b(str, "textToEncrypt");
        return Encryptors.text("U09wQs6svgbl", "a54792ef11d53c68").encrypt(str);
    }
}
```

```java
/* renamed from: com.starhub.newmsa.views.login.b */
/* compiled from: AppLoginFragment.kt */
public final class C4018b extends C3692a implements OnClickListener, C3771a {

    /* ... */

    /* access modifiers changed from: private */
    /* renamed from: q */
    public final void m12519q() {
        EditText editText = (EditText) mo22776a(C3123R.C3125id.etEmail);
        C0889i.m2279a((Object) editText, "etEmail");
        String obj = editText.getText().toString();
        EditText editText2 = (EditText) mo22776a(C3123R.C3125id.etPassword);
        C0889i.m2279a((Object) editText2, "etPassword");
        String obj2 = editText2.getText().toString();
        if (!(!C4548g.m13400a((CharSequence) obj)) || !(!C4548g.m13400a((CharSequence) obj2))) {
            m12502a(obj, obj2);
            return;
        }
        LinearLayout linearLayout = (LinearLayout) mo22776a(C3123R.C3125id.llValidationError);
        C0889i.m2279a((Object) linearLayout, "llValidationError");
        linearLayout.setVisibility(8);
        mo22039j();
        C3513a aVar = C3513a.f6377a;
        StringBuilder sb = new StringBuilder();
        sb.append(obj2);
        sb.append(Global.UNDERSCORE);
        sb.append(System.currentTimeMillis());
        String c = aVar.mo21552c(sb.toString());
        C0889i.m2279a((Object) c, "encryptedPassword");
        MssoLoginRequest mssoLoginRequest = new MssoLoginRequest(obj, c, "mystarhub");
        LoginViewModel loginViewModel = this.f7414c;
        if (loginViewModel != null) {
            LiveData a = loginViewModel.mo22767a(mssoLoginRequest);
            if (a != null) {
                a.observe(this, new C4020b(this));
                return;
            }
        }
        mo22038i();
    }

    /* ... */
}
```

### Frida and Android Emulator

Since I do not have a relatively new Android phone lying around, I have to use a rooted emulator to do runtime inspection

```bash
# Install APK
adb install ~/Downloads/starhub.apk

# Launch AVD with API 23 (it is the latest version that is rooted)
/home/yaowei/Android/Sdk/emulator/emulator -list-avds
/home/yaowei/Android/Sdk/emulator/emulator -writable-system -selinux disabled -avd Nexus_5X_API_23

# Install Frida
# https://github.com/frida/frida/releases
# Download frida-server-{version}-android-x86.xz
> adb push frida-server-x86 /data/local/tmp/
> adb shell "chmod 755 /data/local/tmp/frida-server-x86"
> adb shell "/data/local/tmp/frida-server-x86 &"

# Inspect/Find running processess
# for StarHub, you'll get com.starhub.csselfhelp
frida-ps -U | grep starhub

# Load script on Process
frida -l ~/Desktop/script.js com.starhub.csselfhelp
```

#### Basic Frida

Resources:
- https://github.com/iddoeldor/frida-snippets#trace-class
- Google 'Frida examples' or something like that


#### Using Frida to Trace Class

See [https://github.com/iddoeldor/frida-snippets#trace-class](https://github.com/iddoeldor/frida-snippets#trace-class)

```java
var Color = {
    RESET: "\x1b[39;49;00m", Black: "0;01", Blue: "4;01", Cyan: "6;01", Gray: "7;11", Green: "2;01", Purple: "5;01", Red: "1;01", Yellow: "3;01",
    Light: {
        Black: "0;11", Blue: "4;11", Cyan: "6;11", Gray: "7;01", Green: "2;11", Purple: "5;11", Red: "1;11", Yellow: "3;11"
    }
};

/**
 *
 * @param input. 
 *      If an object is passed it will print as json 
 * @param kwargs  options map {
 *     -l level: string;   log/warn/error
 *     -i indent: boolean;     print JSON prettify
 *     -c color: @see ColorMap
 * }
 */
var LOG = function (input, kwargs) {
    kwargs = kwargs || {};
    var logLevel = kwargs['l'] || 'log', colorPrefix = '\x1b[3', colorSuffix = 'm';
    if (typeof input === 'object')
        input = JSON.stringify(input, null, kwargs['i'] ? 2 : null);
    if (kwargs['c'])
        input = colorPrefix + kwargs['c'] + colorSuffix + input + Color.RESET;
    console[logLevel](input);
};

var printBacktrace = function () {
    Java.perform(function() {
        var android_util_Log = Java.use('android.util.Log'), java_lang_Exception = Java.use('java.lang.Exception');
        // getting stacktrace by throwing an exception
        LOG(android_util_Log.getStackTraceString(java_lang_Exception.$new()), { c: Color.Gray });
    });
};

function traceClass(targetClass) {
    var hook;
    try {
        hook = Java.use(targetClass);
    } catch (e) {
        console.error("trace class failed", e);
        return;
    }

    var methods = hook.class.getDeclaredMethods();
    hook.$dispose();

    var parsedMethods = [];
    methods.forEach(function (method) {
        var methodStr = method.toString();
        var methodReplace = methodStr.replace(targetClass + ".", "TOKEN").match(/\sTOKEN(.*)\(/)[1];
         parsedMethods.push(methodReplace);
    });

    uniqBy(parsedMethods, JSON.stringify).forEach(function (targetMethod) {
        traceMethod(targetClass + '.' + targetMethod);
    });
}

function traceMethod(targetClassMethod) {
    var delim = targetClassMethod.lastIndexOf('.');
    if (delim === -1)
        return;

    var targetClass = targetClassMethod.slice(0, delim);
    var targetMethod = targetClassMethod.slice(delim + 1, targetClassMethod.length);

    var hook = Java.use(targetClass);
    var overloadCount = hook[targetMethod].overloads.length;

    LOG({ tracing: targetClassMethod, overloaded: overloadCount }, { c: Color.Green });

    for (var i = 0; i < overloadCount; i++) {
        hook[targetMethod].overloads[i].implementation = function () {
            var log = { '#': targetClassMethod, args: [] };

            for (var j = 0; j < arguments.length; j++) {
                var arg = arguments[j];
                // quick&dirty fix for java.io.StringWriter char[].toString() impl because frida prints [object Object]
                if (j === 0 && arguments[j]) {
                    if (arguments[j].toString() === '[object Object]') {
                        var s = [];
                        for (var k = 0, l = arguments[j].length; k < l; k++) {
                            s.push(arguments[j][k]);
                        }
                        arg = s.join('');
                    }
                }
                log.args.push({ i: j, o: arg, s: arg ? arg.toString(): 'null'});
            }

            var retval;
            try {
                retval = this[targetMethod].apply(this, arguments); // might crash (Frida bug?)
                log.returns = { val: retval, str: retval ? retval.toString() : null };
            } catch (e) {
                console.error(e);
            }
            LOG(log, { c: Color.Blue });
            return retval;
        }
    }
}

// remove duplicates from array
function uniqBy(array, key) {
    var seen = {};
    return array.filter(function (item) {
        var k = key(item);
        return seen.hasOwnProperty(k) ? false : (seen[k] = true);
    });
}


var Main = function() {
    Java.perform(function () { // avoid java.lang.ClassNotFoundException
        [
            // "java.io.File",
            'com.starhub.newmsa.views.login.b'
        ].forEach(traceClass);
    });
};

Java.perform(Main);
```

The above example will hook onto the class `com.starhub.newmsa.views.login.b` and display any method calls to it. This
will allow me to figure out what parameters are passed to it. This is kind of similar to Cycript on iOS.