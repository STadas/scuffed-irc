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
from datetime import datetime
from pytz import reference

motd = "No MOTD set."

try:
	motd = "MOTD: " + open("motd.txt", "r").read()
except:
	pass

hostname = "the-inn"
version = "0.1"
today = datetime.now()
tz_name = reference.LocalTimezone().tzname(today)
create_time = today.strftime("%Y-%M-%D, %H:%M:%S")

IP = "::1"
PORT = 6667

serv_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.bind((IP, PORT))
serv_sock.listen(5)
serv_sock.setblocking(False)

sockets_list = [serv_sock]
clients = {}
channels = {}


print("\033[1;36mServer started.")
print("Current time:", create_time, tz_name)
print(f"Listening on [{IP}]:{PORT}\033[0m")

def parse_sock(cl_sock: socket.socket) -> bytes:
	try:
		data = cl_sock.recv(2 ** 10)
		if len(data) != 0:
			print("\n\033[1;36m== RAW data START ==\033[0m")
			print(data)
			print("\033[1;34m=== RAW data END ===\033[0m\n")
		else:
			return False
	except BrokenPipeError: # thank u vincent
		return False
	except ConnectionResetError:
		return False
	return data


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


def send_msg(cl_sock: socket.socket, msg: str):
	cl_sock.sendall(bytes((msg + ("\r\n" if msg[len(msg)-2:] != "\r\n" else "")).encode("utf-8")))


def new_client(cl_sock: socket.socket, cl_addr: tuple):
	nick = ""
	realname = ""

	while nick == "" or realname == "":
		data = parse_sock(cl_sock)
		if data is False:
			print("FAILED connection from", cl_addr)
			return

		data_str = data.decode("utf-8")

		if comm_contents(data_str, "NICK") is not None:
			nick = comm_contents(data_str, "NICK")
		if comm_contents(data_str, "USER") is not None:
			realname = comm_contents(data_str, "USER", ' ')
		
	print(f"NICK \"{nick}\"")
	print(f"USER \"{realname}\"")

	sockets_list.append(cl_sock)
	clients[cl_sock] = {
		'nick': nick,
		'realname': realname
	}

	send_msg(cl_sock, f":{hostname} 001 {nick} :Yo, welcome to The Inn.")
	send_msg(cl_sock, f":{hostname} 002 {nick} :Your host is {hostname}, running version {version}")
	send_msg(cl_sock, f":{hostname} 003 {nick} :This server was created {create_time} {tz_name}")
	send_msg(cl_sock, f":{hostname} 251 {nick} :There {f'are {len(clients)} users' if len(clients) != 1 else 'is 1 user'} on the server.")
	send_msg(cl_sock, f":{hostname} 422 {nick} :{motd}")


while True:
	# print("IN_WHILE")
	read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
	# print("GOT_SOCKS")

	for sock in read_sockets:
		# print("IN_FOR")
		if sock == serv_sock:
			cl_sock, cl_addr = serv_sock.accept()
			print("OPEN connection from", cl_addr)
			new_client(cl_sock, cl_addr)
			print(clients)
			# print("CAP_DONE")
		else:
			data = parse_sock(sock)

			if data is False or data.decode("utf-8").find("QUIT") != -1:
				print("CLOSE connection from", cl_addr)
				sockets_list.remove(sock)
				del clients[sock]
				print(clients)
				continue

			user = clients[sock]
			print(f"[{user['nick']}/{user['realname']}]: ")

	# print("EXIT_FOR")