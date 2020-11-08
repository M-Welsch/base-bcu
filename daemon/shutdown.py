import logging
import os
from threading import Timer
from time import sleep


class ShutdownController:
    def __init__(self, sbu_communicator, scheduler, display, config_shutdown, stop_threads):
        self._sbu_communicator = sbu_communicator
        self._scheduler = scheduler
        self._display = display
        self._config_shutdown = config_shutdown
        self.stop_threads = stop_threads
        self._shutdown_timer = Timer(15 * 60, self.suggest_shutdown)
        self._shutdown_flag = False

    def seconds_to_next_bu_to_sbu(self):
        seconds_to_next_bu = self._scheduler.seconds_to_next_bu()
        # subtract 5 minutes so the bcu has enough time to start up.
        # Moreover SBU shouldn't be forced to write 0 to its CMP register (Won't do it anyway)
        if seconds_to_next_bu > 333:
            seconds_to_next_bu -= 300
        self._sbu_communicator.send_seconds_to_next_bu_to_sbu(seconds_to_next_bu)

    def initiate_shutdown_process(self):
        self._display.write("Shutdown", "Waiting 5s")
        sleep(5)
        logging.info("Shutting down")
        self._sbu_communicator.send_human_readable_timestamp_next_bu(self._scheduler.next_backup_scheduled())
        self.seconds_to_next_bu_to_sbu()
        self._sbu_communicator.send_shutdown_request()
        self.stop_threads()
        self.shutdown_base()

    def suggest_shutdown(self):
        self._shutdown_flag = True

    def reset_shutdown_flag(self):
        self._shutdown_flag = False

    @property
    def shutdown_flag(self):
        return self._shutdown_flag

    def reset_shutdown_timer(self):
        logging.info("Setting")
        if self._shutdown_timer.is_alive():
            self.cancel_shutdown_timer()
        timeout_in_seconds = self._config_shutdown["idle_time_before_shutdown_in_minutes"] * 60
        self._shutdown_timer = Timer(timeout_in_seconds, self.suggest_shutdown)
        self._shutdown_timer.start()
        self.reset_shutdown_flag()

    def cancel_shutdown_timer(self):
        if self._shutdown_timer.is_alive():
            self._shutdown_timer.cancel()

    def terminate(self):
        logging.info("Shutdown Controller: Terminating ...") # Fixme: take class name out of logging msg once logger is properly implemented
        self.cancel_shutdown_timer()

    @staticmethod
    def shutdown_base():
        os.system("shutdown -h now")  # TODO: os.system() is deprecated. Replace with subprocess.call().