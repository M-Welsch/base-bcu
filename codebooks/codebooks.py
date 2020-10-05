from collections import namedtuple


class TCP_Codebook():
	def __init__(self):
		Command = namedtuple('Command', 'Awaiting_Response, Timeout')
		self._commands = {
			"readout_hdd_parameters": Command(Awaiting_Response=True, Timeout=10),
			"test_mounting": Command(Awaiting_Response=False, Timeout=10),
			"seconds_to_next_bu_to_sbc": Command(Awaiting_Response=False, Timeout=10),
			"terminate_daemon": Command(Awaiting_Response=False, Timeout=10),
			"terminate_daemon_and_shutdown": Command(Awaiting_Response=False, Timeout=10)
		}
		self._commands_awaiting_response = [name for name, params in self._commands.items() if params.Awaiting_Response]

	@property
	def commands(self):
		return self._commands

	@property
	def commands_awaiting_response(self):
		return self._commands_awaiting_response


# class WebApp_Daemon_Codebook():

class SBC_Codebook():
	command_prefixes = {
		"Display Write String": "DS:",
		"Display Dim": "DD:",
		"LED Dim": "LD",
		"Current Consumption": "CC",
		"Temperature": "TP"
	}
	commands = {"Shutdown Request": "SR"}
