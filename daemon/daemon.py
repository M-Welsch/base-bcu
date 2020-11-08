from typing import Dict, List
from datetime import timedelta

from base.codebooks.codebooks import *
from base.common.tcp import TCPServerThread
from base.webapp.webapp import Webapp
from base.schedule.scheduler import BaseScheduler
from base.backup.backup import BackupManager
from base.daemon.mounting import MountManager
from base.daemon.shutdown import ShutdownController
from base.common.utils import *
from base.common.readout_hdd_parameters import readout_parameters_of_all_hdds
from base.sbu_interface.sbu_updater import *
from base.sbu_interface.sbu_communicator import *
from base.hmi.display import *
from base.hmi.hmi import HumanMachineInterface
from base.common.debug_utils import copy_logfiles_to_nas


class BaseStatus:
    def __init__(self):
        self.backup_in_progress_flag = False
        self.backup_finished_flag = False
        self.shutdown_flag = False
        self.terminate_flag = False


class Daemon:
    def __init__(self, autostart_webapp: bool = True):
        self._autostart_webapp = autostart_webapp
        self._tcp_command_queue = Queue()
        self._tcp_codebook = TCP_Codebook()
        self._config = Config.global_instance()
        self._scheduler = BaseScheduler()
        self._mount_manager = MountManager()
        self._hardware_control = HWCTRL.global_instance()
        self._backup_manager = BackupManager(self._mount_manager, self.set_backup_finished_flag)
        self._tcp_server_thread = TCPServerThread(queue=self._tcp_command_queue)
        self._webapp = Webapp()
        self._start_sbu_communicator_on_hw_rev3_and_set_sbu_rtc()
        self._display = Display(self._sbu_communicator)
        self._shutdown_controller = ShutdownController(
            self._sbu_communicator, self._scheduler, self._display, self.stop_threads)
        self._sbu_updater = SbuUpdater()
        self._hmi = HumanMachineInterface()
        self._status = BaseStatus()
        self._display_menu_pointer = 'Main'
        self.start_threads_and_mainloop()

    def _start_sbu_communicator_on_hw_rev3_and_set_sbu_rtc(self):
        if self._hardware_control.get_hw_revision() == 'rev3':
            self._sbu_communicator = SbuCommunicator.global_instance()

    def start_threads_and_mainloop(self):
        self._hardware_control.start()
        self._tcp_server_thread.start()
        if self._autostart_webapp:
            self._webapp.start()
        self.mainloop()

    def stop_threads(self):
        self._hmi.write_priority_message_to_display("Goodbye", "BCU stopping")
        self._sbu_communicator.terminate()  # needs active hwctrl to shutdown cleanly!
        self._hardware_control.terminate()
        self._tcp_server_thread.terminate()
        self._webapp.terminate()
        self._shutdown_controller.terminate()
        copy_logfiles_to_nas()

    def mainloop(self):
        self._sbu_communicator.set_display_brightness_percent(self._config.config_hmi["display_default_brightness"])
        self._hmi_show_main_menu()
        logging.info(
            f"Next Backup scheduled at {self._scheduler.next_backup_scheduled()}, "
            f"in {self._scheduler.seconds_to_next_bu()} seconds. "
            f"Current Time: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        self._status.terminate_flag = False
        while not self._status.terminate_flag:
            sleep(self._config.main_loop_interval)
            status_quo = self._look_up_status_quo()
            command_list = self._derive_command_list(status_quo)
            self._execute_command_list(command_list)

        if self._status.shutdown_flag:
            self._shutdown_controller.initiate_shutdown_process()
        else:
            self.stop_threads()

    def _hmi_show_main_menu(self):
        self._hmi.write_priority_message_to_display("BaSe   show IP > ", "          Demo >")

    def set_backup_finished_flag(self):
        self._status.backup_finished_flag = True

    def _look_up_status_quo(self) -> Dict:
        status_quo = {
            "pressed_buttons": self._hardware_control.pressed_buttons(),
            "tcp_commands": [],
            "backup_scheduled_for_now": self._scheduler.is_backup_scheduled(),
            "backup_finished": self._status.backup_finished_flag,
            "shutdown_scheduled": self._shutdown_controller.shutdown_flag
        }
        while not self._tcp_command_queue.empty():
            status_quo["tcp_commands"].append(self._tcp_command_queue.get())
            self._tcp_command_queue.task_done()
        # TODO: consider weather
        if status_quo_not_empty(status_quo):
            logging.debug(f"Command Queue contents: {status_quo}")  # TODO: Let mainloop really spam the log?
        return status_quo

    def _derive_command_list(self, status_quo: Dict) -> List[str]:
        command_list = []
        if "backup_full" in status_quo["tcp_commands"]:
            command_list.append("backup_full")
        if "test_mounting" in status_quo["tcp_commands"]:
            return ["mount"]
        if "test_unmounting" in status_quo["tcp_commands"]:
            return ["unmount"]
        if "test_docking" in status_quo["tcp_commands"]:
            return ["dock"]
        if "test_undocking" in status_quo["tcp_commands"]:
            return ["undock"]
        if "reload_config" in status_quo["tcp_commands"]:
            command_list.append("reload_config")
        if "update_sbu" in status_quo["tcp_commands"]:
            return ["update_sbu"]
        if "readout_hdd_parameters" in status_quo["tcp_commands"]:
            return ["readout_hdd_parameters"]
        if "new_buhdd" in status_quo["tcp_commands"]:
            return ["enter_new_buhdd_in_config.json"]
        if "show_status_info" in status_quo["tcp_commands"]:
            command_list.append("show_status_info")
        if "setup_shutdown_timer" in status_quo["tcp_commands"]:
            command_list.append("setup_shutdown_timer")
        if status_quo["pressed_buttons"][0]:  # show IP Adress on Display
            command_list.append("show_ip_on_display")
        if status_quo["pressed_buttons"][1]:  # demo
            command_list.extend(["dock", "wait", "undock"])
        if "terminate_daemon" in status_quo["tcp_commands"]:
            command_list.append("terminate_daemon")
        if "terminate_daemon_and_shutdown" in status_quo["tcp_commands"]:
            command_list.append("terminate_daemon_and_shutdown")
        if "seconds_to_next_bu_to_sbc" in status_quo["tcp_commands"]:
            self._shutdown_controller.seconds_to_next_bu_to_sbu()
        if status_quo["backup_scheduled_for_now"]:
            command_list.append("backup_full")
        if status_quo["backup_finished"]:
            self._status.backup_finished_flag = False
            self._schedule_backup_for_longterm_test()
            command_list.extend(["cleanup_after_backup", "unmount", "undock", "setup_shutdown_timer"])
        if status_quo["shutdown_scheduled"]:
            self._shutdown_controller.reset_shutdown_flag()
            command_list.append("terminate_daemon_and_shutdown")
        if command_list:
            print("command list:", command_list)
        return command_list

    @staticmethod
    def _extract_sbc_filename_from_commmand(status_quo_tcp_commands: List) -> str:
        sbc_filename = None
        for entry in status_quo_tcp_commands:
            if entry[:10] == "update_sbc":
                sbc_filename = entry[:14]
        return sbc_filename

    def _execute_command_list(self, command_list: List[str]):
        for command in command_list:
            try:
                if command == "dock":
                    self._hardware_control.dock_and_power()
                elif command == "wait":
                    sleep(10)
                elif command == "undock":
                    self._hardware_control.unpower_and_undock()
                elif command == "mount":
                    self._mount_manager.mount_hdd()
                elif command == "unmount":
                    self._mount_manager.unmount_hdd()
                elif command == "backup_full":
                    self._scheduler.backup_suggested = False
                    self._backup_manager.backup()
                elif command == "cleanup_after_backup":
                    self._backup_manager.cleanup_after_backup()
                elif command == "reload_config":
                    self._config.reload()
                elif command == "show_status_info":
                    self.get_status()
                elif command == "show_ip_on_display":
                    self.show_ip_address_on_display()
                elif command == "terminate_daemon":
                    self._status.terminate_flag = True
                    return True
                elif command == "terminate_daemon_and_shutdown":
                    self._shutdown_controller.initiate_shutdown_process()
                    self._status.shutdown_flag = True
                    return True
                elif command == "update_sbu":
                    self.update_sbu()
                elif command == "readout_hdd_parameters":
                    self.read_and_send_hdd_parameters()
                elif command == "enter_new_buhdd_in_config.json":
                    self.update_bu_hdd_in_config_file()
                elif command == "setup_shutdown_timer":
                    self._shutdown_controller.reset_shutdown_timer()
                else:
                    raise RuntimeError(f"'{command}' is not a valid command!")
            except Exception as e:
                logging.error(f"Some command went somehow wrong: {e}")
                raise e
        return False

    def _schedule_backup_for_longterm_test(self):
        last_bu_interval = self._config.config_schedule["test_key"]
        next_bu_interval = 2*last_bu_interval
        self._config.config_schedule["test_key"] = next_bu_interval
        then = datetime.now() + timedelta(seconds=next_bu_interval*60)
        self._config.config_schedule["backup_frequency"] = "Weekly"
        self._config.config_schedule["day_of_week"] = int(then.strftime("%w"))
        self._config.config_schedule["hour"] = int(then.strftime("%H"))
        self._config.config_schedule["minute"] = int(then.strftime("%M"))
        self._config.update()
        self._scheduler.setup_schedule()

    def get_status(self):
        pass  # TODO: Avoid non-functional code on master branch!
        # # TODO: implement hardware status retrieval
        # # next_bu_time = read_next_scheduled_backup_time()
        # seconds_to_next_bu = self._scheduler.seconds_to_next_bu()
        # next_backup_scheduled = self._scheduler.next_backup_scheduled()
        # next_backup_scheduled_string = next_backup_scheduled.strftime("%d.%m.%Y %H:%M")
        # # self._hardware_control.display("{}\nETA {}s".format(next_backup_scheduled_string, seconds_to_next_bu), 2)
        # # uncomment line above once SBC-Display forwarding works!
        #
        # # TODO: send to Webapp if it asks for status ...
        # backups_present = list_backups_by_age(self._config.config_mounting["backup_hdd_mount_point"])

    def show_ip_address_on_display(self):
        if self._display_menu_pointer == 'IP':
            self._hmi_show_main_menu()
            self._display_menu_pointer = 'Main'
        else:
            ip = get_ip_address()
            self._hmi.write_priority_message_to_display('Local IP: back >', ip)
            self._display_menu_pointer = 'IP'

    def update_sbu(self):
        print("updating SBU")
        self._hmi.write_priority_message_to_display("Updating SBU", "Firmware")
        self._sbu_communicator.terminate()
        self._sbu_updater.update_sbu()
        self._start_sbu_communicator_on_hw_rev3_and_set_sbu_rtc()
        self._hmi_show_main_menu()
        # SBC_U = SBC_Updater()
        # SBC_U.update_sbc()

    def read_and_send_hdd_parameters(self):
        try:
            # request the result one second before TCP Server's timeout elapses
            timeout = self._tcp_codebook.commands["readout_hdd_parameters"].Timeout - 1
            wait_for_new_device_file(timeout)
        except RuntimeError as e:
            print(e)
        answer = readout_parameters_of_all_hdds()
        self._tcp_server_thread.write_answer(answer)

    def update_bu_hdd_in_config_file(self):
        self._config.write_BUHDD_parameter_to_tmp_config_file()
