'''
https://tools.ietf.org/html/rfc2810 - general architecture
https://tools.ietf.org/html/rfc2812 - client/server comms
https://docs.python.org/3.9/howto/sockets.html - python socket docs
https://medium.com/python-pandemonium/python-socket-communication-e10b39225a4c - tutorial 1
https://realpython.com/python-sockets/ - tutorial 2
https://ircv3.net/specs/core/capability-negotiation.html - stuff i found on CAP, the initial command, though most likely wont matter
https://stackoverflow.com/questions/5163255/regular-expression-to-match-irc-nickname - regex for nicks
'''
"""
TODO: check all replycodes and if their replies are done correctly; limit length of names, msg, etc.
TODO: Line 131(ascii), 155 (ascii), 209 (topics), 237 (comm_contents), 260 (comm_contents)
"""

import socket
import select
from datetime import datetime
from pytz import reference

MOTD = "No MOTD set."

try:
	MOTD = "MOTD: " + open("motd.txt", "r").read()
except:
	pass

today = datetime.now()
TZ_NAME = reference.LocalTimezone().tzname(today)
CREATE_TIME = today.strftime("%Y-%m-%d, %H:%M:%S")
HOST_NAME = "the-inn"
VERSION = "0.1"
SERVER_NAME = "Yulgar's Inn"
SERVER_IP = "::1"
PORT = 6667

SERV_SOCK = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
SERV_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERV_SOCK.bind((SERVER_IP, PORT))
SERV_SOCK.listen(5)
SERV_SOCK.setblocking(False)

sockets_list = [SERV_SOCK]
clients_list = []
channels_dict = {}

print("\033[1;36mServer started.")
print("Current time:", CREATE_TIME, TZ_NAME)
print(f"Listening on [{SERVER_IP}]:{PORT}\033[0m")


def console_print(msg: str):
	print("\033[1;33m////\033[0m", msg)


def comm_contents(data_str: str, comm_str: str, to_str: str = '\r') -> str:
	if data_str.find(comm_str) == -1:
		return False
	
	from_index = data_str.find(comm_str) + len(comm_str) + 1

	find_to = data_str.find(to_str, from_index)
	find_r = data_str.find('\r', from_index)
	find_n = data_str.find ('\n', from_index)

	to_index = find_to if find_to != -1 else (find_r if find_r != -1 else (find_n if find_n != -1 else len(data_str)-1))

	return data_str[from_index:to_index + 1]


class Client:
	# Initialises Client with: client socket, nick, realname, ip, channels
	def __init__(self, sock: socket.socket, nick: str, realname: str, addr: tuple, channels: [], welcome: bool):
		self.sock = sock
		self.nick = nick
		self.realname = realname
		self.addr = addr
		self.channels = []
		self.welcome = welcome
		self.func_names = {
			"PING": self.ping,
			"JOIN": self.join_channel,
			"WHO": self.who,
			"PRIVMSG": self.privmsg,
			"PART": self.leave_channel,
			"NICK": self.set_nick,
			"USER": self.set_realname,
			"QUIT": self.leave_server
		}


	@staticmethod
	# Finds client by socket
	def find_client(sock: socket.socket):
		for cl in clients_list:
			if cl.sock == sock:
				return cl
	


	# Definitions of functions by IRC commands for easier usage in the main loop
	def comm_func(self, func: str, arg):
		func_names = self.func_names
		return func_names[func](arg)
	

	# Receives and parses message(s)/command(s) from client socket
	def parse_data(self) -> bytes:
		try:
			data = self.sock.recv(2 ** 20)
			if len(data) != 0:
				print("\033[1;32m>>\033[0m", f"\033[37m{data}\033[0m")
			else:
				return False
		except BrokenPipeError: # thank u vincent
			return False
		except ConnectionResetError:
			return False
		return data


	# Sends message(s)/commmand(s) to client socket
	def send_msg(self, msg: str):
		try:
			msg = bytes((msg + ("\r\n" if msg[len(msg)-2:] != "\r\n" else "")).encode("utf-8"))
			print("\033[1;31m<<\033[0m", f"\033[37m{msg}\033[0m")
			self.sock.sendall(msg)
		except BrokenPipeError:
			console_print("FAILED TO SEND")
		except ConnectionResetError:
			console_print("FAILED TO SEND")


	# Sets nick for the Client
	def set_nick(self, nick: str):
		console_print(f"NICK {nick}")

		rejected_symbols = "\"`'!/\\%+-*#@$&;:,.\r\n\t [](){}" #TODO try using the ASCII library to check
		for s in rejected_symbols:
			if nick.find(s) != -1:
				console_print("REJECTED nick (has any of: [!:@ *;#\"`'/\\%+-.\\r\\n\\t$,&])")
				self.send_msg("nick rejected. (has any of: [!:@ *;#\"`'/\\%+-.\\r\\n\\t$,&])\r\nPlease pick a different nick without any of those symbols.")
				return False

		for cl in clients_list:
			if cl.nick == nick and cl.sock != self.sock:
				console_print("REJECTED nick (already taken)")
				self.send_msg("nick rejected. (already taken)\r\nPlease pick a different nick")
				return False

		self.send_msg(f":{self.nick}!{self.realname}@{SERVER_IP} NICK {nick}")
		self.nick = nick

		if self.nick != "" and self.realname != "":
			self.__welcome()
		
		return True


	# Sets realname for the Client
	def set_realname(self, data_str: str):
		realname = data_str[data_str.find(":") + 1:]
		console_print(f"USER {realname}")

		rejected_symbols = "\"`'!/%+*#@$&;:,.\r\n\t ()" #TODO try using the ASCII library to check
		for s in rejected_symbols:
			if realname.find(s) != -1:
				console_print("REJECTED realname (has any of: [\"`'!/%+*#@$&;:,.\\r\\n\\t<space>()])")
				self.sock.send_msg("realname rejected. (has any of: [\"`'!/%+*#@$&;:,.\\r\\n\\t<space>()])\r\nPlease reconnect with a different realname without any of those symbols.")
				return False

		self.realname = realname

		if self.nick != "" and self.realname != "":
			self.__welcome()

		return True
	

	# Adds new client to clients list and sends appropriate messaging
	def add(self):
		sockets_list.append(self.sock)
		clients_list.append(self)
	

	def __welcome(self):
		self.send_msg(f":{HOST_NAME} 001 {self.nick} :Yo, welcome to {SERVER_NAME}.")
		self.send_msg(f":{HOST_NAME} 002 {self.nick} :Your host is {HOST_NAME}, running VERSION {VERSION}")
		self.send_msg(f":{HOST_NAME} 003 {self.nick} :This server was created {CREATE_TIME} {TZ_NAME}")
		self.send_msg(f":{HOST_NAME} 251 {self.nick} :There {f'are {len(clients_list)} users' if len(clients_list) != 1 else 'is 1 user'} on the server.")
		self.send_msg(f":{HOST_NAME} 422 {self.nick} :{MOTD}")

		console_print(f"NEW USER '{self.nick}!{self.realname}'")
	

	# Adds client to a channel, creates one if it doesn't exist
	def join_channel(self, channel_name: str):
		if channel_name[0] != '#':
			self.send_msg(f":{HOST_NAME} 403 {self.nick} {channel_name} :No such channel")
			return
		
		try:
			console_print(f"TRYING TO JOIN CHANNEL '{channel_name}'")
			channels_dict[channel_name].append(self)
		except KeyError:
			console_print(f"NOT FOUND, CREATING CHANNEL '{channel_name}'")
			channels_dict[channel_name] = [self]
		
		self.channels.append(channel_name)
		for chan_cl in channels_dict[channel_name]:
			chan_cl.send_msg(f":{self.nick}!{self.realname}@{SERVER_IP} JOIN {channel_name}")

		self.send_msg(f":{HOST_NAME} 331 {self.nick} {channel_name} :No topic") #TODO topics
		
		usr_list_msg = f":{HOST_NAME} 353 {self.nick} = {channel_name} :"
		nick_buffer = ""
		for chan_cl in channels_dict[channel_name]:
			if len(nick_buffer) > 32:
				self.send_msg(usr_list_msg + nick_buffer)
				nick_buffer = ""
			nick_buffer += chan_cl.nick + " "
		if len(nick_buffer) > 0:
			self.send_msg(usr_list_msg + nick_buffer)
			
		self.send_msg(f":{HOST_NAME} 366 {self.nick} {channel_name} :End of NAMES list")

		console_print(f"JOINED CHANNEL '{channel_name}'")
		
	
	# Responds to WHO command from the client, sends vebose list of clients in the channel
	def who(self, channel_name: str):
		for chan_cl in channels_dict[channel_name]:
			self.send_msg(f":{HOST_NAME} 352 {self.nick} {channel_name} {self.realname} {self.addr[0]} {HOST_NAME} {chan_cl.nick} H :0 {chan_cl.realname}")

		self.send_msg(f":{HOST_NAME} 315 {self.nick} {channel_name} :End of WHO list")


	# Sends a message to a channel or another client
	def privmsg(self, target_and_msg: str):
		target = target_and_msg[:target_and_msg.find(' ')]
		msg = target_and_msg[target_and_msg.find(':') + 1:] #TODO try to use comm_contents

		if len(bytes(msg.encode("utf-8"))) > (2 ** 10):
			self.send_msg("No spammerino")
			return

		if target[0] != '#':
			for priv_cl in clients_list:
				if priv_cl.nick == target:
					priv_cl.send_msg(f":{self.nick}!{self.realname}@{SERVER_IP} PRIVMSG {target} :{msg}")
					return
			self.send_msg(f":{HOST_NAME} 403 {self.nick} {target} :No such channel or user")

		else:
			for chan_cl in channels_dict[target]:
				if chan_cl.sock == self.sock:
					continue
				chan_cl.send_msg(f":{self.nick}!{self.realname}@{SERVER_IP} PRIVMSG {target} :{msg}")


	# Removes client from channel
	def leave_channel(self, channel_and_comment: str):
		channel_name = channel_and_comment[:channel_and_comment.find(' ')]
		comment = channel_and_comment[channel_and_comment.find(':') + 1:] #TODO try to use comm_contents

		console_print(f"LEAVING CHANNEL {channel_name}")

		if channel_name[0] != '#':
			console_print(f"CANT FIND CHANNEL {channel_name}")
			self.send_msg(f":{HOST_NAME} 403 {self.nick} {channel_name} :No such channel")
			return
		
		for chan_cl in channels_dict[channel_name]:
			chan_cl.send_msg(f":{self.nick}!{self.realname}@{SERVER_IP} PART {channel_name} :{comment}")
		
		channels_dict[channel_name].remove(self)
		if len(channels_dict[channel_name]) == 0:
			console_print(f"NO USERS IN '{channel_name}', DELETING")
			del channels_dict[channel_name]
		self.channels.remove(channel_name)
			
	
	def ping(self, lag_str: str):
		self.send_msg(f":{HOST_NAME} PONG {socket.getfqdn(self.addr[0])} :{lag_str}")


	def leave_server(self, comment: str):
		console_print(f"CLOSE connection from {self.addr}")

		for chan_name in list(self.channels):
			self.comm_func("PART", f"{chan_name} :{comment}")
		
		self.send_msg(f":{self.nick}!{self.realname}@{SERVER_IP} QUIT :{comment}")
		
		sockets_list.remove(self.sock)
		clients_list.remove(self)

		console_print(f"NUMBER OF CLIENTS: {len(clients_list)}")


while True:
	read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

	for sock in read_sockets:
		if sock == SERV_SOCK:
			cl_sock, cl_addr = SERV_SOCK.accept()
			console_print(f"OPEN connection from {cl_addr}")
			new_cl = Client(cl_sock, "", "", cl_addr, [], False)
			new_cl.add()
			console_print(f"NUMBER OF CLIENTS: {len(clients_list)}")
		else:
			client = Client.find_client(sock)
			data = client.parse_data()

			if data is False:
				client.leave_server("Leaving server")
			
			else:
				data_str = data.decode("utf-8")

				for line in data_str.splitlines():
					for func_key in client.func_names.keys():
						if comm_contents(line, func_key) and ((client.nick != "" and client.realname != "") or (func_key == "NICK" or func_key == "USER")):
							client.comm_func(func_key, comm_contents(line, func_key))
							break
