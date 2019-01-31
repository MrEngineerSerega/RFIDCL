import serial
import serial.tools.list_ports
import time

def DetectingArduino():
    stports = serial.tools.list_ports.comports()
    portsAvalible = []
    for port in stports:
        portsAvalible.append(port.device)
    print(portsAvalible)

    for port in portsAvalible:
        print(port)
        serSP = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)
        serSP.write(b'RFIDSDetect')
        mess = serSP.readline()
        print(mess)
        if mess.decode() == "GOOD\r\n":
            print("GoodPort")
            return port
        else:
            print("BadPort")


ser = serial.Serial(DetectingArduino(), 115200, timeout=1)

while True:
    print(ser.readline().decode(), end='')
    time.sleep(0.1)
