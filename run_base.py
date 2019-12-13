import os
import daemon

from common.tcp import TCPServerThread

def main():
	print("starting daemon...")
	with daemon.DaemonContext(working_directory=os.getcwd()):
		msg_from_tcp = ["0"]

		srv = TCPServerThread(msg_from_tcp)
		srv.start()
		while not msg_from_tcp[-1] == "kill me":
			continue
		srv.terminate()

if __name__ == '__main__':
	main()

# stderr, stdout auf irgendwas lesbares umbiegen
# logger implementieren