import socket
import rsa
import sqlite3
import sys
import hashlib
from threading import Thread
from functools import partial
from Crypto.Cipher import AES
from Crypto import Random
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie

SERVER_IP = "localhost"
SERVER_PORT = 8888


class StartForm(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("StartForm.ui", self)

        anim = QMovie("media\waiting.gif")
        self.label.setMovie(anim)
        anim.start()

        self.keys_exchange()

    def keys_exchange(self):
        sock = socket.socket()
        sock.connect((SERVER_IP, SERVER_PORT))

        encryption = Encryptor()
        key, nonce = encryption.create_aes()

        encryption.set_rsa_pub_key(sock.recv(1024))

        sock.send(encryption.rsa_encrypt(key + nonce))

        sock.recv(1024)

        self.main_form = MainForm(sock, encryption)
        self.main_form.show()
        self.hide()


class MainForm(QMainWindow):
    def __init__(self, sock, encryption):
        super().__init__()
        self.sock = sock
        self.encryption = encryption
        uic.loadUi("MainForm.ui", self)

        self.menuFile.addAction("Open")
        self.menuFile.addAction("Open Recent")
        self.menuFile.addAction("Save")
        self.menuFile.addAction("Add File", self.add_file, "CTRL+N")
        self.menuFile.addSeparator()
        self.menuFile.addAction('Settings')
        self.menuFile.addAction('Exit')

    def add_file(self):
        self.new_file = NewFileForm(self.sock, self.encryption)
        self.new_file.show()


class NewFileForm(QWidget):
    def __init__(self, sock, encryption):
        super().__init__()
        self.sock = sock
        self.encryption = encryption
        uic.loadUi("NewFileForm.ui", self)

        self.browsei_btn.clicked.connect(self.browsei)
        self.browseo_btn.clicked.connect(self.browseo)
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.hide)

    def browsei(self):
        filename = QFileDialog.getOpenFileName(self, "Выберите файл")[0]
        self.input_edt.setText(filename)

    def browseo(self):
        filename = QFileDialog.getSaveFileName(self, "Сохранить",
                                               filter="*.enc")[0]
        self.output_edt.setText(filename)

    def ok(self):
        short_name = self.input_edt.text().split("/")[-1]
        file_enc = Encryptor()
        key = b"".join(file_enc.create_aes())
        input = open(self.input_edt.text(), "rb")
        encrypted_file = file_enc.aes_encrypt(input.read())
        hash = hashlib.sha256(encrypted_file).hexdigest()
        input.close()
        data = b":".join((b"0",
                          short_name.encode(),
                          key,
                          str(self.lvl_spin.value()).encode(),
                          hash.encode()))
        print(data)
        enc = self.encryption.aes_encrypt(data)
        print(enc)
        self.sock.send(enc)

        output = open(self.output_edt.text(), "wb")
        output.write(encrypted_file)
        output.close()


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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    start_form = StartForm()
    start_form.show()
    app.exec_()
