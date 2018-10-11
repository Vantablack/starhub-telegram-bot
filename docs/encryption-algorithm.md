# StarHub Password Encryption Technique

## Reverse Engineering Stage

Using [\[GitHub\] skylot/jadx](https://github.com/skylot/jadx) to decompile [My StarHub](https://play.google.com/store/apps/details?id=com.starhub.csselfhelp&hl=en_US) app, I started digging through the source code.

There are 3 parts to this documentation

1) How StarHub encrypts/decrypt the **plaintext password** and **hub id email** to the local SQLite DB (Android)

2) How StarHub encrypts/decrypt the **plaintext password** for HTTPS request payload

3) Implementing the algorithm in Python


### Encryption/Decryption from SQLite DB (Android)

``` java
import java.security.Key;
import java.security.spec.AlgorithmParameterSpec;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
```

#### Encryption to SQLite

``` java
public static String encrypt(String str) throws Exception {
    byte[] bytes = "2eobgrwapapifsxa".getBytes();
    AlgorithmParameterSpec ivParameterSpec = new IvParameterSpec("jsfkew4plc20mnds".getBytes());
    Key secretKeySpec = new SecretKeySpec(bytes, "AES");
    Cipher instance = Cipher.getInstance("AES/CBC/PKCS5Padding");
    instance.init(1, secretKeySpec, ivParameterSpec);   // 1: ENCRYPT_MODE
    return Base64.encodeToString(instance.doFinal(str.getBytes()), 0);
}
```

#### Decryption from SQLite

``` java
public static String decrypt(String str) throws Exception {
    byte[] bytes = "2eobgrwapapifsxa".getBytes();
    AlgorithmParameterSpec ivParameterSpec = new IvParameterSpec("jsfkew4plc20mnds".getBytes());
    Key secretKeySpec = new SecretKeySpec(bytes, "AES");
    Cipher instance = Cipher.getInstance("AES/CBC/PKCS5Padding");
    instance.init(2, secretKeySpec, ivParameterSpec);   // 2: DECRYPT_MODE
    return new String(instance.doFinal(Base64.decode(str, 0)));
}
```

### Encryption/Decryption for HTTPS Request Payload

This part involves 2 Strings, the **password** and the **salt**.

The **password** and **salt** was retrieved from a class (class name obfuscated) under the package `com.starhub.csselfhelp.utils`.

``` java
PRODUCTION(
 "https://fapi.starhub.com/MyStarhub",
 "http://fapi.starhub.com/MyStarhub",
 "https://login.starhubgee.com.sg/sso/api/common",
 "FZH9f/TWMhNR2vLC7M0Tuhy/8jG1it8H",
 "1d2286041ee068cb1561f2838e0e71fa",
 "U09wQs6svgbl",        // password
 "a54792ef11d53c68",    // salt
 "https://starhubvocsurveys.com/backend/web/survey?feed_id=",
 "https://login.starhubgee.com.sg/msso/bapp/api/ssoredirect?src_siteid=mystarhub&src_token=%1$s&src_session_id=%2$s&tgt_siteid=jprotect&cb=https://juniorprotect.starhub.com/user/index.html"
)
```

### Encryption Algorithm

From what I understand, the encryption library uses:

- 256 bit AES encryption and derives the secret key using PKCS #5's PBKDF2.
- The provided salt is expected to be hex-encoded and at least 8 bytes in length
- Also applies a random 16 byte initialization vector (IV) to ensure uniqueness

``` java
import org.springframework.security.crypto.encrypt.Encryptors;

public static String encrypt(String str) {
    String password = "U09wQs6svgbl";
    String salt = "a54792ef11d53c68";
    return Encryptors.text(password, salt).encrypt(str);
}
```

#### Format of Input Password

In one of the Android Activity, I found this line of code (obfuscated)

``` java
private MSSOLoginResponse a() {
    this.b = com.starhub.csselfhelp.chat.utils.a.c(this.b + "_" + System.currentTimeMillis());
    return com.starhub.csselfhelp.network.c.b(MyStarHubApplication.d().b("KEY_MSSO_LOGIN_URL", ""), String.format("{\"user_id\":\"%1$s\",\"user_password\":\"%2$s\",\"site_id\":\"%3$s\"}", new Object[] {
  this.a, this.b, "mystarhub"
 }), this.f.b);
}
```

`this.b` represents the **plaintext password**. What StarHub does is that it appends `_` plus `current time in milliseconds` behind the plaintext password.

> Input: `YOURPASSWORD_1529598919501`

> Output: `1a5ebfa6e2445515451af1f7fa2b45ec8385514c660f611ec1ee05478d0083b96848e2f064f51100242b9242e956dff1`

### Implementing in Python

Someone has already done the implementation in Python thanks to this article: http://www.tmarthal.com/2016/07/using-pycrypto-with-spring-cryptospring.html [archive.org link here](https://web.archive.org/web/*/http://www.tmarthal.com/2016/07/using-pycrypto-with-spring-cryptospring.html)

The fork of the GitHub Gist is available here: https://gist.github.com/Vantablack/21ec8f66974c5b22627d120671a71d9c