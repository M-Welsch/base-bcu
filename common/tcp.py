#!/usr/bin/python3

import threading
import socket


class TCPServerThread(threading.Thread):
	def __init__(self, queue, logger, port=12346, max_requests=5):
		super(TCPServerThread, self).__init__()
		self._logger = logger
		self._exit_flag = False
		self._command_queue = queue

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		self.host = socket.gethostname()                           
		self.port = port
		self.max_requests = max_requests

		self.sock.settimeout(1.0)
		self.sock.bind((self.host, self.port))                                  

	def run(self):
		self.sock.listen(self.max_requests)
		print("Listening to port %i" % self.port)
		while not self._exit_flag:
		    # establish a connection
		    try:
		    	clientsocket, addr = self.sock.accept()
		    except socket.timeout:
		    	continue

		    print("Got a connection from %s" % str(addr))
		    
		    data = clientsocket.recv(1024).decode("utf-8")
		    print(data)
		    self._command_queue.put(data)

		    msg = "Action " + str(data) + " successful!\n"
		    clientsocket.send(msg.encode('utf-8'))
		    clientsocket.close()

	def terminate(self):
		self._exit_flag = True


class TCPClientInterface:
	def __init__(self, port=12345, max_bytes=1024):
		self.host = socket.gethostname()
		self.port = port
		self.max_bytes = max_bytes

	def send(self, msg):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		sock.connect((self.host, self.port))
		sock.send(msg.encode("utf8"))
		ans = sock.recv(self.max_bytes)
		sock.close()
		return ans.decode('utf-8')
