import os
import daemon
from queue import Queue

from time import sleep

from base.common.base_queues import LoggingQueue
from base.common.config import Config
from base.schedule.scheduler import Scheduler
from base.common.base_logging import Logger
from base.hwctrl.hwctrl import HWCTRL
from base.common.tcp import TCPServerThread
from base.webapp.index import Webapp

class Daemon():
	def __init__(self, autostart_webapp=True, daemonize=True):
		self._autostart_webapp = autostart_webapp
		self._logging_queue = LoggingQueue()
		self._log = self._logging_queue.push_msg
		self._command_queue = Queue()
		self._config = Config("base/config.json")
		self._scheduler = Scheduler()
		self._logger = Logger(self._logging_queue, self._logging_queue.work_off_msg)
		self._hardware_control = HWCTRL(self._logging_queue.push_msg)
		self._hardware_control_feedback_flags = self._hardware_control.status
		self._tcp_server_thread = TCPServerThread(queue=self._command_queue, push_msg=self._logging_queue.push_msg)
		self._webapp = Webapp()
		if daemonize:
			self.run_as_daemon()
		else:
			self.run_not_as_daemon()


	def start_threads_and_mainloop(self):
		self._logger.start()
		self._hardware_control.start()
		self._tcp_server_thread.start()
		if self._autostart_webapp:
			self._webapp.start()
		self.mainloop()

	def run_as_daemon(self):
		print("starting daemon...")
		self._log("started base as daemon")
		with daemon.DaemonContext(working_directory=os.getcwd()):
			# sys.stdout = self._logging_queue fixme
			# sys.stderr = self._logging_queue fixme
			self.start_threads_and_mainloop()

	def run_not_as_daemon(self):
		self._log("started BaSe without daemon (debug-mode)")
		print("starting daemon (not actually as daemon)...")
		self.start_threads_and_mainloop()

	def mainloop(self):
		while True:
			sleep(1)  # TODO: Make configurable
			# check HW status
			# log sth
			# work off tcp queue
			# consider schedule