import logging
import pickle

from Crypto.Cipher import AES
from Crypto.Util import Counter


class Cipher(object):
    def __init__(self, key):
        self.key = key
        self.delimiter = '\x08'
        # create cipher object from key
        ctr1 = Counter.new(128)
        ctr2 = Counter.new(128)
        self.enc_cipher = AES.new(key, AES.MODE_CTR, counter=ctr1)
        self.dec_cipher = AES.new(key, AES.MODE_CTR, counter=ctr2)

    def encrypt(self, msg):
        length = 16 - (len(msg) % 16)
        msg += chr(length) * length
        return self.enc_cipher.encrypt(msg)

    def decrypt(self, msg):
        dec = self.dec_cipher.decrypt(msg)
        dec = dec[:-ord(dec[-1])]
        return dec

    def encrypt2(self, msg):
        cipher = AES.new(self.key, AES.MODE_CCM)
        return pickle.dumps((cipher.nonce, cipher.encrypt(msg), cipher.digest()))

    def decrypt2(self, msg):
        nonce, ciphertext, mac = pickle.loads(msg)
        cipher = AES.new(self.key, AES.MODE_CCM, nonce)
        plaintext = cipher.decrypt(ciphertext)
        try:
            cipher.verify(mac)
            return plaintext
        except ValueError:
            logging.warning("Key incorrect or message corrupted ({})".format(plaintext))
