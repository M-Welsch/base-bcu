import RPi.GPIO as GPIO
from time import sleep
import serial

ser = serial.Serial('/dev/ttyS2')
if ser.isOpen() == True:
	ser.close()

_serial_connection = serial.Serial()

_serial_connection.baudrate = 9600
_serial_connection.port = '/dev/ttyS2'
_serial_connection.timeout = 1
_serial_connection.open()

_serial_connection.write(b'hello')
_serial_connection.close()