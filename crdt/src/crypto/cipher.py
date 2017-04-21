import logging
import pickle

from Crypto.Cipher import AES


class Cipher(object):
    def __init__(self, key):
        self.key = key

    def encrypt(self, msg):
        cipher = AES.new(self.key, AES.MODE_CCM)
        return pickle.dumps((cipher.nonce, cipher.encrypt(msg), cipher.digest()))

    def decrypt(self, msg):
        nonce, ciphertext, mac = pickle.loads(msg)
        cipher = AES.new(self.key, AES.MODE_CCM, nonce)
        plaintext = cipher.decrypt(ciphertext)
        try:
            cipher.verify(mac)
            return plaintext
        except ValueError:
            logging.warning("Key incorrect or message corrupted ({})".format(plaintext))
