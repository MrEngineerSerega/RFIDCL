import serial
import time

ser = serial.Serial('COM3', 9600)
ser.

while True:
    time.sleep(0.1)
    print(ser.readline().decode())
