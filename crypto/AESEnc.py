from Crypto.Cipher import AES
from Crypto import Random

class AESEnc:
    def __init__(self, key) -> None:
        self.key = bytes(key, 'utf-8')

    def pad(self, s):
        return s + b"\0" * (AES.block_size - len(s) % AES.block_size)
    
    def encrypt(self, data):
        data = self.pad(data)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(data)

    def decrypt(self, ciphertext):
        iv = ciphertext[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext[AES.block_size:])
        return plaintext.rstrip(b"\0")
