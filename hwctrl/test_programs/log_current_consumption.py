import smbus
from time import sleep
import datetime

bus = smbus.SMBus(1)

try:
	while True:

		data = bus.read_i2c_block_data(0x4d, 1)
		# print("Data[0] = %r\nData[1] = %r" % (data[0], data[1]))
		cDate = datetime.datetime.now().strftime("%Y_%m_%d")
		cTime = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M.%S")
		logfile = open("current_consumption"+cDate+".log", "a")
		logfile.write(str(cTime) + ", " + str(data[0]) + str(data[1]) + "\n")
		logfile.close()
		sleep(0.1)
except KeyboardInterrupt:
	pass
