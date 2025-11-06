# AES.py
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

class AESCipher:
    def __init__(self, key=None):
        self.key = key or get_random_bytes(16)

    def generate_key(self):
        self.key = get_random_bytes(16)
        return base64.b64encode(self.key).decode()

    def encrypt(self, plaintext):
        cipher = AES.new(self.key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

    def decrypt(self, ciphertext_b64):
        data = base64.b64decode(ciphertext_b64)
        nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()
