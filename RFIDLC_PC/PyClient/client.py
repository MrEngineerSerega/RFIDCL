import socket
import rsa
import sqlite3
import sys
import hashlib
import time
import os
from serial import Serial
from serial.tools import list_ports
from functools import partial
from Crypto.Cipher import AES
from Crypto import Random
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QThread, pyqtSignal

SERVER_IP = "localhost"
SERVER_PORT = 8888


class Encryptor:
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.key = None

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
        self.key = key
        return key

    def set_aes(self, key):
        self.key = key

    def aes_encrypt(self, data):
        aes = AES.new(self.key, AES.MODE_EAX)
        data, tag = aes.encrypt_and_digest(data)
        return data + aes.nonce

    def aes_decrypt(self, data):
        aes = AES.new(self.key, AES.MODE_EAX, nonce=data[-16:])
        return aes.decrypt(data[:-16])


class StartForm(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("StartForm.ui", self)

        anim = QMovie("media/waiting.gif")
        self.label.setMovie(anim)
        anim.start()
        self.show()

        self.loading = Loading()
        self.loading.loaded.connect(self.draw_main_form)
        self.loading.failed.connect(self.failed)
        self.loading.start()

    def draw_main_form(self, sock, encryption, serial):
        self.main_form = MainForm(sock, encryption, serial)
        self.main_form.show()
        self.hide()

    def failed(self, msg):
        QMessageBox(QMessageBox.Information, "RFIDLC", msg).exec_()
        sys.exit()


class Loading(QThread):
    loaded = pyqtSignal(socket.socket, Encryptor, Serial)
    failed = pyqtSignal(str)

    def run(self):
        try:
            sock, encryption = self.keys_exchange()
            serial = self.detect_port()
            if not os.path.exists("files"):
                os.makedirs("files")
            open("recents.list", "a+")

            if not serial:
                raise ValueError

            self.loaded.emit(sock, encryption, serial)
        except ConnectionRefusedError:
            self.failed.emit("Failed to connect to server")
        except ValueError:
            self.failed.emit("Сould not find the reader")


    def keys_exchange(self):
        sock = socket.socket()
        sock.connect((SERVER_IP, SERVER_PORT))

        encryption = Encryptor()
        key = encryption.create_aes()

        encryption.set_rsa_pub_key(sock.recv(1024))

        sock.send(encryption.rsa_encrypt(key))

        sock.recv(1024)

        return sock, encryption

    def detect_port(self):
        serial = Serial(baudrate=115200, timeout=3)
        for port in list_ports.comports():
            serial.setPort(port.device)
            serial.open()

            time.sleep(2)
            serial.write(b"3")
            if serial.readline() == b"GOOD\r\n":
                print("detected on {}".format(port.device))
                return serial
            serial.close()


class MainForm(QMainWindow):
    def __init__(self, sock, encryption, serial):
        super().__init__()
        self.sock = sock
        self.encryption = encryption
        self.serial = serial
        uic.loadUi("MainForm.ui", self)

        self.menuFile.addAction("Open", self.open_enc_file, "Ctrl+O")
        self.menuFile.addAction("Add File", self.add_file, "Ctrl+N")
        self.menuFile.addSeparator()
        self.menuFile.addAction('Exit', sys.exit)

        self.add_file_btn.clicked.connect(self.add_file)
        self.open_enc_file_btn.clicked.connect(self.open_enc_file)
        self.open_btn.clicked.connect(self.open_file)
        self.recent_list.itemDoubleClicked.connect(self.open_selected_file)

        self.update_recent()


    def add_file(self):
        self.new_file = NewFileForm(self.sock, self.encryption)
        self.new_file.added.connect(self.added)
        self.new_file.show()

    def open_file(self):
        self.open_external = OpenExternal(self.file)
        self.open_external.start()

    def open_enc_file(self):
        try:
            file = QFileDialog.getOpenFileName(self, "Выберите файл",
                                               filter="*.enc")[0]
            if not file:
                raise ValueError

            self.checking_form = CheckingForm()
            self.checking_form.show()

            self.checking = CheckingKey(self.sock, self.encryption,
                                        self.serial, file)
            self.checking.checked.connect(self.opened)
            self.checking_form.closed.connect(self.close_checking)
            self.checking.start()
            self.add_recent(file)
        except ValueError:
            pass

    def open_selected_file(self, item):
        file = item.text()

        self.checking_form = CheckingForm()
        self.checking_form.show()

        self.checking = CheckingKey(self.sock, self.encryption,
                                    self.serial, file)
        self.checking.checked.connect(self.opened)
        self.checking_form.closed.connect(self.close_checking)
        self.checking.start()
        self.add_recent(file)

    def added(self, file):
        self.add_recent(file)

    def opened(self, state, file):
        self.file = file
        if state:
            self.checking_form.status_lbl.setText("Access Granted")
            file_data = open(file, "rb")
            try:
                self.preview.setPlainText(file_data.read().decode())
            except UnicodeDecodeError:
                self.preview.setPlainText(str(file_data.read()))
            file_data.close()
            self.open_btn.setEnabled(True)
        else:
            self.checking_form.status_lbl.setText("Access Denied")
            self.checking.start()

    def close_checking(self):
        self.checking.terminate()

    def update_recent(self):
        rec = open("recents.list", "r")
        self.recent_list.clear()
        self.recent_list.addItems(map(str.strip, rec.readlines()[::-1]))
        rec.close()

    def add_recent(self, file):
        rec = open("recents.list", "a+")
        recents = rec.readlines()
        path = os.path.abspath(file) + "\n"
        rec.write(path)
        rec.close()

        self.update_recent()


class OpenExternal(QThread):
    def __init__(self, file):
        self.file = file
        super().__init__()

    def run(self):
        os.system('"{}"'.format(self.file))


class NewFileForm(QWidget):
    added = pyqtSignal(str)

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
        try:
            short_name = self.input_edt.text().split("/")[-1]
            file_enc = Encryptor()
            key = file_enc.create_aes()
            input = open(self.input_edt.text(), "rb")
            encrypted_file = file_enc.aes_encrypt(input.read())
            hash = hashlib.sha256(encrypted_file).hexdigest()
            input.close()
            data = b":".join((b"0",
                              short_name.encode(),
                              key,
                              str(self.lvl_spin.value()).encode(),
                              hash.encode()))
            self.sock.send(self.encryption.aes_encrypt(data))

            self.sock.recv(1024)

            output = open(self.output_edt.text(), "wb")
            output.write(encrypted_file)
            output.close()

            msg = QMessageBox(QMessageBox.Information,
                              "RFIDLC",
                              "File was added successfully")
            msg.exec_()
            self.hide()
            self.added.emit(os.path.abspath(self.output_edt.text()))
        except FileNotFoundError:
            msg = "File not found"
            QMessageBox(QMessageBox.Information, "RFIDLC", msg).exec_()


class CheckingForm(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi("CheckingForm.ui", self)

    def closeEvent(self, arg):
        print(arg)
        self.closed.emit()


class CheckingKey(QThread):
    checked = pyqtSignal(bool, str)
    def __init__(self, sock, encryption, serial, file):
        super().__init__()
        self.sock = sock
        self.encryption = encryption
        self.serial = serial
        self.file = file

    def run(self):
        self.serial.flushInput()
        self.serial.timeout = None
        user_key = self.serial.readline().decode().strip()

        file = open(self.file, "rb")
        file_data = file.read()
        file.close()
        hash = hashlib.sha256(file_data).hexdigest()

        data = b":".join((b"1",
                         user_key.encode(),
                         hash.encode()))
        self.sock.send(self.encryption.aes_encrypt(data))

        resp = self.encryption.aes_decrypt(self.sock.recv(2048))
        if resp != b"err":
            self.serial.write(b"1")
            file_name, *file_key = resp.split(b":")
            file_key = b"".join(file_key)
            file_enc = Encryptor()
            file_enc.set_aes(file_key)
            file = open("files/{}".format(file_name.decode()), "wb")
            file.write(file_enc.aes_decrypt(file_data))
            file.close()
            self.checked.emit(True, os.path.abspath(file.name))
        else:
            self.serial.write(b"2")
            self.checked.emit(False, "")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    start_form = StartForm()
    app.exec_()
