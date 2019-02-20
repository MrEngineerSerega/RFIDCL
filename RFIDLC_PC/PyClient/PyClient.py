import serial
import serial.tools.list_ports
import time
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
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

    yield stream.write(RSAPublicKey + b'\r\n')
    encSessionKey = yield stream.read_until(b"\r\n")
    encSessionKey = encSessionKey.replace(b'\r\n', b'')
    RSACipher = PKCS1_OAEP.new(RSAPrivateKey)
    sesionKey = RSACipher.decrypt(encSessionKey)

    while True:
        encAESCipher = AES.new(sesionKey, AES.MODE_EAX)

        arduinoRecive = ser.readline().replace(b'\r\n', b'')
        if arduinoRecive.decode() != "":
            encMessage, encTag = encAESCipher.encrypt_and_digest(arduinoRecive)
            yield stream.write(encAESCipher.nonce + b':' + encMessage + b':' + encTag + b'\r\n')
            logging.info("Sent to server: %s", encAESCipher.nonce + b':' + encMessage + b':' + encTag + b'\r\n')
            encResponse = yield stream.read_until(b"\r\n")
            encResponse = encResponse.replace(b'\r\n', b'')
            logging.info("Response from server: %s", encResponse)
            decNonce, encMessage, decTag = encResponse.split(b':')
            decAESCipher = AES.new(sesionKey, AES.MODE_EAX, nonce=decNonce)
            decMessage = decAESCipher.decrypt(encMessage)
            try:
                decAESCipher.verify(decTag)
                logging.info("Decrypted message: %s", decMessage)
            except ValueError:
                logging.error("Key incorrect or message corrupted")
                continue








logging.info("Programm is started")
RSAPrivateKey = RSA.generate(2048)
logging.debug("Private key: %s", RSAPrivateKey)
RSAPublicKey = RSAPrivateKey.publickey().export_key()
logging.debug("Public key: %s", RSAPublicKey)


ser = serial.Serial(DetectingArduino(), 115200, timeout=1)
IOLoop.current().run_sync(send_message)
