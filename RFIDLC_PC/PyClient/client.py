import asyncio
import rsa
from Crypto.Cipher import AES
from Crypto import Random

SERVER_IP = "localhost"
SERVER_PORT = 8888


class Encryptor:
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.aes = None

    def set_rsa_pub_key(self, key):
        self.public_key = rsa.PublicKey.load_pkcs1(key)

    def create_rsa_pair(self, size=512):
        self.public_key, self.private_key = rsa.newkeys(size)
        return self.public_key.save_pkcs1()

    def rsa_encrypt(self, data: bytes):
        return rsa.encrypt(data, self.public_key)

    def rsa_decrypt(self, data: bytes):
        return rsa.decrypt(data, self.private_key)

    def create_aes(self, size=24):
        key = Random.new().read(size)
        self.aes = AES.new(key, AES.MODE_EAX)
        return key, self.aes.nonce

    def set_aes(self, key, nonce):
        self.aes = AES.new(key, AES.MODE_EAX, nonce=nonce)

    def aes_encrypt(self, data):
        return b"".join(self.aes.encrypt_and_digest(data))

    def aes_decrypt(self, data):
        # self.aes.verify(tag)
        return self.aes.decrypt(data[:-16])


async def main(loop):
    reader, writer = await asyncio.open_connection(SERVER_IP, SERVER_PORT,
                                                   loop = loop)

    encryption = Encryptor()
    key, nonce = encryption.create_aes()

    encryption.set_rsa_pub_key(await reader.read(1024))

    writer.write(encryption.rsa_encrypt(key + nonce))
    await writer.drain()

    await reader.read(1024)

    writer.write(encryption.aes_encrypt(b"helloworld"))
    await writer.drain()

    writer.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
