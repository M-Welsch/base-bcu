import os
import daemon
from queue import Queue

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
		self._hardware_control_feedback_flags = {}
		self._logging_queue = LoggingQueue()
		self._command_queue = Queue()
		self._config = Config("base/config.json")
		self._scheduler = Scheduler()
		self._logger = Logger(self._logging_queue, self._logging_queue.work_off_msg)
		self._hardware_control = HWCTRL(self._hardware_control_feedback_flags, self._logging_queue.push_msg)
		self._tcp_server_thread = TCPServerThread(queue=self._command_queue, push_msg=self._logging_queue.push_msg)
		self._webapp = Webapp()
		if daemonize:
			self.run_as_daemon()
		else:
			self.run_not_as_daemon()


	def start_threads(self):
		self._logger.start()
		self._hardware_control.start()
		self._tcp_server_thread.start()
		if self._autostart_webapp:
			self._webapp.start()

	def run_as_daemon(self):
		print("starting daemon...")
		self._logger.append_to_queue("started base as daemon")
		with daemon.DaemonContext(working_directory=os.getcwd()):
			self.start_threads()

	def run_not_as_daemon(self):
		self._logger.append_to_queue("started BaSe without daemon (debug-mode)")
		print("starting daemon (not actually as daemon)...")
		self.start_threads()