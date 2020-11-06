import os
import sys
import glob

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(path_to_module)

from base.common.utils import get_sbu_fw_uploads_folder, run_external_command_as_generator_shell


class SbuUpdater:
	def __init__(self, hwctrl):
		self._hwctrl = hwctrl

	def update_sbu(self):
		self._hwctrl.enable_receiving_messages_from_attiny()
		self._hwctrl.set_attiny_serial_path_to_sbc_fw_update()

		sbc_fw_filename = self._get_filename_of_newest_hex_file()
		self._write_hex_file_to_sbu(sbc_fw_filename)

		self._hwctrl.set_attiny_serial_path_to_communication()

	@staticmethod
	def _get_filename_of_newest_hex_file():
		list_of_sbc_fw_files = glob.glob("{}/*".format(get_sbu_fw_uploads_folder()))
		latest_sbc_fw_file = max(list_of_sbc_fw_files, key=os.path.getctime)
		return latest_sbc_fw_file

	@staticmethod
	def _write_hex_file_to_sbu(sbu_fw_filename):
		print("Updating SBC with {}".format(sbu_fw_filename))
		# Fixme: use tty-port from config file
		sbu_program_command = 'sudo su - base -c "pyupdi -d tiny816 -c /dev/ttyS1 -f {}"'.format(sbu_fw_filename)
		for line in run_external_command_as_generator_shell(sbu_program_command):
			print(line)


if __name__ == '__main__':

	from base.common.config import Config
	from base.hwctrl.hwctrl import *

	_config = Config("/home/base/base/config.json")
	_hardware_control = HWCTRL.global_instance(_config.config_hwctrl)

	SBUU = SbuUpdater(_hardware_control)
	SBUU.update_sbu()

	_hardware_control.terminate()
