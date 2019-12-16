import os
import daemon
from queue import Queue

from base.common.base_queues import LoggingQueue
from base.common.config import Config
from base.schedule.scheduler import Scheduler
from base.common.logging import Logger
# from base.hwctrl.hwctrl import HWCTRL
from base.common.tcp import TCPServerThread
from base.webapp.index import Webapp

class Daemon():
	def __init__(self, autostart_webapp=True):
		self._hardware_control_feedback_flags = {}
		self._logging_queue = LoggingQueue()
		self._command_queue = Queue()
		self._config = Config("base/config.json")
		self._scheduler = Scheduler()
		self._logger = Logger(self._logging_queue.work_off_msg)
		# self._hardware_control = HWCTRL(self._hardware_control_feedback_flags, self._logging_queue.push_msg)
		self._tcp_server_thread = TCPServerThread(queue=self._command_queue, push_msg=self._logging_queue.push_msg)
		self._webapp = Webapp()
		print("starting daemon...")
		# with daemon.DaemonContext(working_directory=os.getcwd()):
		self._logger.start()
		# self._hardware_control.start()
		self._tcp_server_thread.start()
		if autostart_webapp:
			self._webapp.start()
