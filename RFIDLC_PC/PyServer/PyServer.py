import logging
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
            sesionKey = get_random_bytes(32)
            RSACipher = PKCS1_OAEP.new(RSAPublicKey)
            encSessionKey = RSACipher.encrypt(sesionKey)
            yield stream.write(encSessionKey + b'\r\n')
            logging.info("Sent to %s: %s" % (clientIP, encSessionKey))
            while True:
                data = yield stream.read_until(b"\r\n")
                logging.info("Received bytes from %s: %s" % (clientIP, data))
                if not data.endswith(b"\r\n"):
                    data = data + b"\r\n"
                yield stream.write(data)
        except StreamClosedError:
            logging.warning("Lost client at host %s", clientIP)
        # except Exception as e:
        #     logging.error(e)

if __name__ == "__main__":
    options.parse_command_line()
    server = EchoServer()
    server.listen(options.port)
    logging.info("Listening on TCP port %d", options.port)
    IOLoop.current().start()
