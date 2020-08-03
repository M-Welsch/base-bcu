#!/usr/bin/python3

import threading
import socket
from collections import namedtuple
from time import sleep, time

from base.codebooks.codebooks import TCP_Codebook


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
		self._codebook = TCP_Codebook
		self.answer_string = ""

		self.sock.settimeout(1.0)
		self.configure_server()

	def configure_server(self):
		try:
			self.sock.bind((self.host, self.port))
		except OSError:
			self.port += 1
			print("Socket blocked. Using port {}".format(self.port))
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

			incoming_message = clientsocket.recv(1024).decode("utf-8")
			print(incoming_message)
			self._command_queue.put(incoming_message)
			self._wait_for_answer_string(incoming_message, 3)
			answer_message = self._compose_answer(incoming_message)
			self._send_message(answer_message, clientsocket)
			clientsocket.close()

	def _send_message(self, answer_message, clientsocket):
		print("sending {} as answer.".format(answer_message))
		clientsocket.send(answer_message.encode('utf-8'))

	def terminate(self):
			self._exit_flag = True

	def _wait_for_answer_string(self, incoming_message, timeout):
		start = time()
		while not self.answer_string:
			if time() - start > timeout:
				print("Answer to {} was not set after {}s".format(incoming_message, timeout))
				break
			sleep(0.1)

	def _compose_answer(self, incoming_message):
		if incoming_message in self._codebook.commands_awaiting_response:

			answer_message = self.answer_string
			self.answer_string = ""
		else:
			answer_message = "Action " + str(incoming_message) + " successful!\n"
		return answer_message

	def write_answer(self, answer_string):
		self.answer_string = answer_string


class TCPClientInterface:
	def __init__(self, port=12346, max_bytes=1024):
		self.host = socket.gethostname()
		self.port = port
		self.max_bytes = max_bytes

	def send(self, msg):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect((self.host, self.port))
		except ConnectionRefusedError:
			raise ConnectionRefusedError
		sock.send(msg.encode("utf8"))
		ans = sock.recv(self.max_bytes)
		sock.close()
		return ans.decode('utf-8')


class TCPClientThread(threading.Thread):
	def __init__(self):
		super(TCPServerThread, self).__init__()
		self._exit_flag = False
		self._host = socket.gethostname()
		self._setup_communication_queue()

	def _setup_communication_queue(self):
		self._communication_queue = []
		self._communication_queue_entry = namedtuple("Communication Queue Entry", "msg_sent msg_received port")

	def run(self):
		while not self._exit_flag:
			sleep(1)

	def send_and_wait_for_answer(self, message, port, max_bytes=1024):
		answer = ""
		[sock, port] = self.open_socket(port)
		sock.send(message.encode("utf8"))
		answer = sock.recv(max_bytes)
		answer = answer.decode('utf-8')
		sock.close()
		self._communication_queue.append(
			self._communication_queue_entry(msg_sent=message, msg_received=answer, port=port))

	def open_socket(self, port):
		connection_trials = 0
		while connection_trials < 2:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				sock.connect((self._host, port))
				break
			except ConnectionRefusedError:
				port += 1
				connection_trials += 1
		return [sock, port]

	def terminate(self):
		self._exit_flag = True

	@property
	def communication_queue(self):
		return self._communication_queue.pop()
