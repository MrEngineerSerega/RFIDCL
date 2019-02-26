from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib

key = input("Ключ шифрования: ")
if key == "rand":
    key = get_random_bytes(32)
print("Ключ шифрования:", key)
encAESCipher = AES.new(key, AES.MODE_EAX)

file = open(input("Путь к файлу: "), mode="rb")
savePath = input("Сохранить как: ")
encFile = open(savePath, mode='wb')

encText, tag = encAESCipher.encrypt_and_digest(file.read())

encFile.write(encAESCipher.nonce)
encFile.write(tag)
encFile.write(encText)

file.close()
encFile.close()

encFile = open(savePath, mode='rb')
print("Хэш зашифрованного файла:", hashlib.sha256(encFile.read()).hexdigest())
encFile.close()
