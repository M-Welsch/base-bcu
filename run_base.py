import sys, os

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(path_to_module)
sys.path.append(path_to_module)

from base.daemon.daemon import Daemon

def main():
	d = Daemon()
	# print("starting daemon...")
	# with daemon.DaemonContext(working_directory=os.getcwd()):
	# 	msg_from_tcp = ["0"]

	# 	srv = TCPServerThread(msg_from_tcp)
	# 	srv.start()
	# 	while not msg_from_tcp[-1] == "kill me":
	# 		continue
	# 	srv.terminate()

if __name__ == '__main__':
	main()

# stderr, stdout auf irgendwas lesbares umbiegen
# logger implementieren