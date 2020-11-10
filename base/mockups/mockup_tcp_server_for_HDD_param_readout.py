#!/usr/bin/python3           # This is server.py file
import socket            
from time import sleep  
import os
import sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)
from base.common.utils import run_external_command_as_generator_shell, readout_hdd_parameters


def start_server():
	# create a socket object
	serversocket = socket.socket(
				socket.AF_INET, socket.SOCK_STREAM) 

	# get local machine name
	host = socket.gethostname()                           

	# get port
	#config = configparser.ConfigParser()
	#config.read('../../../config.ini')
	port = 12346 #config.getint('Daemon','dm_listens_to_port')

	# bind to the port
	serversocket.bind((host, port))                                  

	# queue up to 5 requests
	serversocket.listen(5)
	print("Listening to port %i" % port)

	while True:
		# establish a connection
		clientsocket,addr = serversocket.accept() 

		print("Got a connection from %s" % str(addr))
		
		data = clientsocket.recv(1024)
		print(data)
		if data == b'readout_hdd_parameters':

			[model_number, serial_number] = readout_hdd_parameters_standalone()
			[mn, sn] = readout_hdd_parameters()


			msg = "Model Number: {} Serial Number: {} and MN: {}, SN: {}".format(model_number, serial_number, mn, sn)

		else:
			msg = "Action " + str(data) + " successful!\r\n"
		sleep(2)
		clientsocket.send(msg.encode('ascii'))
		clientsocket.close()


def readout_hdd_parameters_standalone():
	model_number = "No Model Number found"
	serial_number = "No Serial Number found"
	for line in run_external_command_as_generator_shell("sudo hdparm -I /dev/sda"):
		contains_model_number = line.find("Model Number")
		if not contains_model_number == -1:
			model_number = line[contains_model_number+13:].strip()

		contains_serial_number = line.find("Serial Number")
		if not contains_serial_number == -1:
			serial_number = line[contains_serial_number+14:].strip()

	return [model_number, serial_number]


if __name__=="__main__":
	start_server()
