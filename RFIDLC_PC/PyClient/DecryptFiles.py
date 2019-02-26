from Crypto.Cipher import AES

file = open("lorem.enc", mode="rb")
file = file.read()
nonce = file[:16]
tag = file[16:32]
ciphertext = file[32:]
print(nonce)
print(tag)
print(ciphertext)

key = input("Ключ шифрования: ")
decAESCipher = AES.new(key.encode(), AES.MODE_EAX, nonce=nonce)
data = decAESCipher.decrypt_and_verify(ciphertext, tag)
print(data)
