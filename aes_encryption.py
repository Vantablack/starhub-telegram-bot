import binascii

from Crypto import Random
from Crypto.Cipher import AES


class AesCrypt256:
    """
    Source: http://www.tmarthal.com/2016/07/using-pycrypto-with-spring-cryptospring.html
    Backup Gist: https://gist.github.com/Vantablack/21ec8f66974c5b22627d120671a71d9c
    """

    # Based on https://gist.github.com/pfote/5099161
    BLOCK_SIZE = 16

    # To use the null/x00 byte array for the IV
    default_initialization_vector = False

    def __init__(self, default_initialization_vector=False):
        self.default_initialization_vector = default_initialization_vector

    def pkcs5_pad(self, s):
        return s + (self.BLOCK_SIZE - len(s) % self.BLOCK_SIZE) * chr(self.BLOCK_SIZE - len(s) % self.BLOCK_SIZE)

    def pkcs5_unpad(self, s):
        # from https://jhafranco.com/2012/01/16/aes-implementation-in-python/
        return "".join(chr(e) for e in s[:-s[-1]])

    def _encrypt(self, key, value, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        crypted = cipher.encrypt(self.pkcs5_pad(value).encode('utf-8'))

        # check if empty/null initialization vector, and do not prepend if null
        if all(v == 0 for v in iv):
            return crypted
        else:
            # prepend the initialization vector
            return iv + crypted

    def _decrypt(self, key, value, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # unpad the bytes, throw away garbage at end
        return self.pkcs5_unpad(cipher.decrypt(value))

    def encrypt(self, key, value):
        if self.default_initialization_vector:
            return self._encrypt(key, value, bytes(bytearray(16)))
        else:
            iv = Random.get_random_bytes(16)
            return self._encrypt(key, value, iv)

    def decrypt(self, key, value):
        if self.default_initialization_vector:
            # we do not have an IV present
            default_iv = bytes(bytearray(16))
            return self._decrypt(key, value, default_iv)
        else:
            iv = value[:16]
            crypted = value[16:]
            return self._decrypt(key, crypted, iv)

    def encryptHex(self, key, value):
        return binascii.hexlify(self.encrypt(key, value))

    def decryptHex(self, key, value):
        return self.decrypt(key, binascii.unhexlify(value))
