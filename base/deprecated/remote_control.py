from common.tcp import TCPClientInterface

cli = TCPClientInterface()

while True:
	msg = input("msg >> ")
	ans = cli.send(msg)
	print(ans)