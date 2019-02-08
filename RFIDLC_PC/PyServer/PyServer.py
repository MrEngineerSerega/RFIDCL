import logging
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.options import options, define

define("port", default=8888, help="TCP port to listen on")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] (%(processName)-10s) %(message)s'
)


class EchoServer(TCPServer):
    @gen.coroutine
    def handle_stream(self, stream, address):
        while True:
            try:
                data = yield stream.read_until(b"\n")
                clientIP = address[0]
                logging.info("Received bytes from %s: %s" % (clientIP, data))
                if not data.endswith(b"\n"):
                    data = data + b"\n"
                yield stream.write(data)
            except StreamClosedError:
                logging.warning("Lost client at host %s", address[0])
                break
            except Exception as e:
                logging.error(e)


if __name__ == "__main__":
    options.parse_command_line()
    server = EchoServer()
    server.listen(options.port)
    logging.info("Listening on TCP port %d", options.port)
    IOLoop.current().start()
