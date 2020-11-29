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
create_time = today.strftime("%Y-%m-%d, %H:%M:%S")

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
		return False
	
	from_index = data_str.find(comm_str) + len(comm_str) + 1

	find_to = data_str.find(to_str, from_index)
	find_r = data_str.find('\r', from_index)
	find_n = data_str.find ('\n', from_index)

	to_index = find_to if find_to != -1 else (find_r if find_r != -1 else (find_n if find_n != -1 else len(data_str)-1))

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

		if comm_contents(data_str, "NICK"):
			nick = comm_contents(data_str, "NICK")
		if comm_contents(data_str, "USER"):
			realname = comm_contents(data_str, "USER", ' ')
		
	print(f"NICK \"{nick}\"")
	print(f"USER \"{realname}\"")

	sockets_list.append(cl_sock)
	clients[cl_sock] = {
		'nick': nick,
		'realname': realname,
		'ip': cl_sock.getpeername()[0],
		'channels': []
	}

	send_msg(cl_sock, f":{hostname} 001 {nick} :Yo, welcome to The Inn.")
	send_msg(cl_sock, f":{hostname} 002 {nick} :Your host is {hostname}, running version {version}")
	send_msg(cl_sock, f":{hostname} 003 {nick} :This server was created {create_time} {tz_name}")
	send_msg(cl_sock, f":{hostname} 251 {nick} :There {f'are {len(clients)} users' if len(clients) != 1 else 'is 1 user'} on the server.")
	send_msg(cl_sock, f":{hostname} 422 {nick} :{motd}")


def join_channel(cl_sock: socket.socket, channel_name: str):
	if channel_name[0] != '#':
		send_msg(cl_sock, f":{hostname} 403 {clients[cl_sock]['nick']} {channel_name} :No such channel")
		# :arsicpc 403 tadz test :No such channel
		return
	
	try:
		print(f"TRYING TO JOIN CHANNEL \"{channel_name}\"")
		channels[channel_name].append(cl_sock)
	except KeyError:
		print(f"CREATING CHANNEL \"{channel_name}\"")
		channels[channel_name] = [cl_sock]
	
	clients[cl_sock]['channels'].append(channel_name)
	for chan_sock in channels[channel_name]:
		send_msg(chan_sock, f":{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}@{IP} JOIN {channel_name}")

	data = parse_sock(cl_sock)
	print(data.decode("utf-8"))

	if not data or comm_contents(data.decode("utf-8"), "MODE") != channel_name:
		if len(channels[channel_name]) == 1:
			del channels[channel_name]
		clients[cl_sock]['channels'].remove(channel_name)
		return

	send_msg(cl_sock, f":{hostname} 331 {clients[cl_sock]['nick']} {channel_name} :No topic")
	
	usr_list_msg = f":{hostname} 353 {clients[cl_sock]['nick']} = {channel_name} :"
	nick_buffer = ""
	for chan_sock in channels[channel_name]:
		if len(nick_buffer) > 32:
			send_msg(cl_sock, usr_list_msg + nick_buffer)
			nick_buffer = ""
		nick_buffer += " " + clients[chan_sock]['nick']
	if len(nick_buffer) > 0:
		send_msg(cl_sock, usr_list_msg + nick_buffer)
		
	send_msg(cl_sock, f":{hostname} 366 {clients[cl_sock]['nick']} {channel_name} :End of NAMES list")
	send_msg(cl_sock, f":{hostname} 324 {clients[cl_sock]['nick']} {channel_name} +")

	data = parse_sock(cl_sock)
	print(data.decode("utf-8"))

	if not data or comm_contents(data.decode("utf-8"), "WHO") != channel_name:
		if len(channels[channel_name]) == 1:
			del channels[channel_name]
		clients[cl_sock]['channels'].remove(channel_name)
		return
	
	for chan_sock in channels[channel_name]:
		send_msg(cl_sock, f":{hostname} 352 {clients[chan_sock]['nick']} {channel_name} {clients[chan_sock]['realname']} {IP} {hostname} {clients[chan_sock]['nick']} H :0 {clients[chan_sock]['realname']}")

	send_msg(cl_sock, f":{hostname} 315 {clients[chan_sock]['nick']} {channel_name} :End of WHO list")

	'''
	<< JOIN #test
	>> :tadz_!arsic@::1 JOIN #test
	<< MODE #test
	<< WHO #test
	>> :arsicpc 331 tadz_ #test :No topic is set
	>> :arsicpc 353 tadz_ = #test :tadz_
	>> :arsicpc 366 tadz_ #test :End of NAMES list
	>> :arsicpc 324 tadz_ #test +
	>> :arsicpc 352 tadz_ #test arsic ::1 arsicpc tadz_ H :0 arsic
	>> :arsicpc 315 tadz_ #test :End of WHO list
	>> :tadz!arsic@::1 JOIN #test
	<< PRIVMSG #test :yooooo
	<< PING LAG1606541568062
	>> :arsicpc PONG arsicpc :LAG1606541568062
	>> :tadz!arsic@::1 PRIVMSG #test :XDDDDD
	<< PART #test :Leaving
	>> :tadz_!arsic@::1 PART #test :Leaving
	<< QUIT :Leaving
	'''


def privmsg(comm_contents: str):
	pass


while True:
	read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

	for sock in read_sockets:
		if sock == serv_sock:
			cl_sock, cl_addr = serv_sock.accept()
			print("OPEN connection from", cl_addr)
			new_client(cl_sock, cl_addr)
			print(clients)
		else:
			data = parse_sock(sock)

			if data is False or data.decode("utf-8").find("QUIT") == 0:
				print("CLOSE connection from", cl_addr)
				sockets_list.remove(sock)
				del clients[sock]
				print(clients)

			elif comm_contents(data.decode("utf-8"), "PING"):
				send_msg(sock, f":{hostname} PONG {socket.getfqdn(clients[sock]['ip'])} :{comm_contents(data.decode('utf-8'), 'PING')}")
			
			elif comm_contents(data.decode("utf-8"), "PRIVMSG"):
				privmsg(comm_contents(data.decode("utf-8"), "PRIVMSG"))

			elif comm_contents(data.decode("utf-8"), "JOIN"):
				join_channel(sock, comm_contents(data.decode("utf-8"), "JOIN"))

			else:
				user = clients[sock]
				print(f"[{user['nick']}/{user['realname']}]: ")
