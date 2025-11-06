# DES.py
from Crypto.Cipher import DES
from Crypto.Random import get_random_bytes
import base64

class DESCipher:
    def __init__(self, key=None):
        self.key = key or get_random_bytes(8)

    def generate_key(self):
        self.key = get_random_bytes(8)
        return base64.b64encode(self.key).decode()

    def pad(self, text):
        while len(text) % 8 != 0:
            text += ' '
        return text

    def encrypt(self, plaintext):
        cipher = DES.new(self.key, DES.MODE_ECB)
        padded_text = self.pad(plaintext)
        ciphertext = cipher.encrypt(padded_text.encode())
        return base64.b64encode(ciphertext).decode()

    def decrypt(self, ciphertext_b64):
        cipher = DES.new(self.key, DES.MODE_ECB)
        ciphertext = base64.b64decode(ciphertext_b64)
        plaintext = cipher.decrypt(ciphertext).decode().rstrip()
        return plaintext
