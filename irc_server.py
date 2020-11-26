'''
https://tools.ietf.org/html/rfc2810 - general architecture
https://tools.ietf.org/html/rfc2812 - client/server comms
https://docs.python.org/3.9/howto/sockets.html - python socket docs
https://medium.com/python-pandemonium/python-socket-communication-e10b39225a4c - tutorial 1
https://realpython.com/python-sockets/ - tutorial 2
https://ircv3.net/specs/core/capability-negotiation.html - stuff i found on CAP, the initial command, though most likely wont matter
'''

import socket
import select

users = {}
channels = {}
hostname = "the hut"
IP = "::1"
PORT = 6667

serv_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.bind((IP, PORT))
serv_sock.listen(5)

sockets_list = [serv_sock]
clients = {}

print("Server started.")

def comm_contents(data_str: str, comm_str: str, to_str: str = '\r') -> str:
	if data_str.find(comm_str) == -1:
		return None
	else:
		from_index = data_str.find(comm_str) + len(comm_str) + 1

	find_to = data_str.find(to_str, from_index)
	find_r = data_str.find('\r', from_index)
	find_n = data_str.find ('\n', from_index)

	to_index = find_to if find_to != -1 else (find_r if find_r != -1 else (find_n if find_n != -1 else len(data_str)-1))

	if data_str.find(comm_str) != -1:
		return data_str[from_index:to_index]


def get_names(cl_sock: socket) -> (str, str):
	nick = ""
	realname = ""

	print("------------------ CAP_START ------------------")

	while nick == "" and realname == "":
		data = cl_sock.recv(2 ** 10)
		print("\033[1;36m== RAW data START ==\033[0m")
		print(data)
		print("\033[1;34m=== RAW data END ===\033[0m")
		print()
		data_str = data.decode("utf-8")

		if comm_contents(data_str, "NICK") is not None:
			nick = comm_contents(data_str, "NICK")
		if comm_contents(data_str, "USER") is not None:
			realname = comm_contents(data_str, "USER", ' ')

		# nick_comm_index = data_str.find("NICK")
		# if nick_comm_index != -1:
		# 	# print("FOUND NICK COMM")
		# 	nick_last_index = data_str.find('\r', nick_comm_index) if data_str.find('\r', nick_comm_index) != -1 else data_str.find('\n', nick_comm_index)
		# 	if nick_last_index != -1:
		# 		# print("FOUND ENDL")
		# 		nick = data_str[nick_comm_index + 5:nick_last_index]
		# 	else:
		# 		# print("NO ENDL")
		# 		nick = data_str[nick_comm_index + 5:]
		# 	print(f"NICK \"{nick}\"")

		# realname_comm_index = data_str.find("USER")
		# if realname_comm_index != -1:
		# 	realname = data_str[realname_comm_index + 5:data_str.find(' ', realname_comm_index + 5)]
		
	print(f"NICK \"{nick}\"")
	print(f"USER \"{realname}\"")

	print("------------------- CAP_END -------------------")


while True:
	read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
	for notified_socket in read_sockets:
		if notified_socket == serv_sock:
			cl_sock, cl_addr = serv_sock.accept()
			print("Connection from", cl_addr)
			get_names(cl_sock)
			