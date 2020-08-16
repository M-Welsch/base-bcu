from collections import namedtuple

class TCP_Codebook():
	def __init__(self):
		Command = namedtuple('Command', 'Awaiting_Response, Timeout')
		self._commands = {"readout_hdd_parameters":Command(Awaiting_Response = True, Timeout = 10),
						  "test_mounting":Command(Awaiting_Response = False, Timeout = 10),
						  "seconds_to_next_bu_to_sbc":Command(Awaiting_Response = False, Timeout = 10),
						  "shutdown_base":Command(Awaiting_Response = False, Timeout = 10)
						  }
		self._create_list_of_commands_awaiting_response()

	def _create_list_of_commands_awaiting_response(self):
		self._commands_awaiting_response = []
		for name, params in self._commands.items():
			if params.Awaiting_Response:
				self._commands_awaiting_response.append(name)

	@property
	def commands(self):
		return self._commands
	
	@property
	def commands_awaiting_response(self):
		return self._commands_awaiting_response
	

#class WebApp_Daemon_Codebook():

class SBC_Codebook():
	command_prefixes = {"Display Write String":"DS:",
						"Display Dim":"DD:",
						"LED Dim":"LD",
						"Current Consumption":"CC"
						}
	commands = {"Shutdown Request":"SR"}