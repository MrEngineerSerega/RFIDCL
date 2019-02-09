import serial
import serial.tools.list_ports
import time
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import logging
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.tcpclient import TCPClient

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def DetectingArduino():
    stports = serial.tools.list_ports.comports()
    portsAvalible = []
    for port in stports:
        portsAvalible.append(port.device)
    logging.debug("Avalible ports: %s", ", ".join(portsAvalible))

    for port in portsAvalible:
        serSP = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)
        serSP.write(b'RFIDSDetect')
        mess = serSP.readline()
        if mess.decode() == "GOOD\r\n":
            logging.info("%s is a good port", port)
            return port
        else:
            logging.debug("%s is a bad port", port)


@gen.coroutine
def send_message():
    stream = yield TCPClient().connect("localhost", "8888")
    while True:
        arduinoRecive = ser.readline()
        if arduinoRecive.decode() != "":
            message = arduinoRecive
            yield stream.write(message)
            logging.info("Sent to server: %s", message)
            reply = yield stream.read_until(b"\r\n")
            logging.info("Response from server: %s", reply.decode().strip())


ser = serial.Serial(DetectingArduino(), 115200, timeout=1)

IOLoop.current().run_sync(send_message)
