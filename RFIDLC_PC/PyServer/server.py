import asyncio
import rsa
from Crypto.Cipher import AES
from Crypto import Random

PORT = 8888


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
        return "".join(self.aes.encrypt_and_digest(data))

    def aes_decrypt(self, data):
        # self.aes.verify(tag)
        return self.aes.decrypt(data[:-16])

async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    print("Incoming connection from: {}:{}".format(addr[0], addr[1]))

    encryption = Encryptor()
    pub = encryption.create_rsa_pair()

    writer.write(pub)
    await writer.drain()

    aes_data = encryption.rsa_decrypt(await reader.read(1024))
    encryption.set_aes(aes_data[:-16], aes_data[-16:])

    writer.write(b"ok")
    await writer.drain()

    print(encryption.aes_decrypt(await reader.read(1024)))

    writer.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = asyncio.start_server(handler, "localhost", PORT, loop=loop)
    server = loop.run_until_complete(connection)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Closing...")
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
