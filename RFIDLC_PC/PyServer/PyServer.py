import logging
import sqlite3
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.options import options, define
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

define("port", default=8888, help="TCP port to listen on")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


class EchoServer(TCPServer):
    @gen.coroutine
    def handle_stream(self, stream, address):
        clientIP = address[0]
        logging.info("%s has been connected", clientIP)
        try:
            RSAExpPublicKey = yield stream.read_until(b"\r\n")
            RSAPublicKey = RSA.import_key(RSAExpPublicKey)
            logging.info("Received rsa public key from %s: %s" % (clientIP, RSAExpPublicKey))
            sesionKey = b':'
            while b':' in sesionKey:
                sesionKey = get_random_bytes(32)
            RSACipher = PKCS1_OAEP.new(RSAPublicKey)
            encSessionKey = RSACipher.encrypt(sesionKey)
            yield stream.write(encSessionKey + b'\r\n')
            logging.info("Sent to %s: %s" % (clientIP, encSessionKey))

            while True:
                encAESCipher = AES.new(sesionKey, AES.MODE_EAX)

                data = yield stream.read_until(b"\r\n")
                data = data.replace(b'\r\n', b'')
                logging.info("Received bytes from %s: %s" % (clientIP, data))
                decNonce, encMessage, decTag = data.split(b':')
                decAESCipher = AES.new(sesionKey, AES.MODE_EAX, nonce=decNonce)
                decMessage = decAESCipher.decrypt(encMessage)
                try:
                    decAESCipher.verify(decTag)
                    logging.info("Decrypted message: %s", decMessage)
                except ValueError:
                    logging.error("Key incorrect or message corrupted")
                    yield stream.write(b"Key incorrect or message corrupted\r\n")
                    continue

                message = b'kek'
                encMessage, encTag = encAESCipher.encrypt_and_digest(message)
                yield stream.write(encAESCipher.nonce + b':' + encMessage + b':' + encTag + b'\r\n')
        except StreamClosedError:
            logging.warning("Lost client at host %s", clientIP)
        except Exception as e:
            logging.error(e)

if __name__ == "__main__":
    db = sqlite3.connect("RFIDDataBase.db")
    cursor = db.cursor()

    options.parse_command_line()
    server = EchoServer()
    server.listen(options.port)
    logging.info("Listening on TCP port %d", options.port)
    IOLoop.current().start()
