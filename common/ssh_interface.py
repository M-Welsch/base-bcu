from paramiko import SSHClient


class SSHInterface:
	def __init__(self, host, user):
		self._client = SSHClient()
		self._client.load_system_host_keys()
		self._client.connect(host, username=user)

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self._client.close()

	def run(self, command):
		response_stdout = ""
		response_stderr = ""
		stdin, stdout, stderr = self._client.exec_command(command)
		stderr_lines = "\n".join([line.strip() for line in stderr])
		if stderr_lines:
			response_stderr = "".join([line for line in stderr])
			if response_stderr:
				print("Unraised Error in 'SSHInterface.run': {}".format(response_stderr))
		else:
			response_stdout = "".join([line for line in stdout])
		return response_stdout


	def run_and_raise(self, command):
		stdin, stdout, stderr = self._client.exec_command(command)
		stderr_lines = "\n".join([line.strip() for line in stderr])
		if stderr_lines:
			raise RuntimeError(stderr_lines)
		else:
			return "".join([line for line in stdout])


def run_commands_over_ssh(host, user, commands):
	streams = {"stdout": [], "stderr": []}
	with SSHClient() as client:
		client.load_system_host_keys()
		client.connect(host, username=user)
		for command in commands:
			stdin, stdout, stderr = client.exec_command(command)
			streams["stdout"].append([line for line in stdout])
			streams["stderr"].append([line for line in stderr])
	return streams