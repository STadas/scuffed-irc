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
TODO: check all replycodes and if their replies are done correctly
TODO: Line 131(ascii), 155 (ascii), 209 (topics), 237 (comm_contents), 260 (comm_contents)
"""

import socket
import select
from datetime import datetime
from pytz import reference

motd = "No MOTD set."
server_name = "Yulgar's Inn"

try:
	motd = "MOTD: " + open("motd.txt", "r").read()
except:
	pass

SERVER_NAME = "the-inn"
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
clients_list = []
channels_dict = {}


print("\033[1;36mServer started.")
print("Current time:", create_time, tz_name)
print(f"Listening on [{IP}]:{PORT}\033[0m")

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

	return data_str[from_index:to_index]


class Client:
	# Initialises Client with: client socket, nick, realname, ip, channels
	def __init__(self, sock: socket.socket, nick: str, realname: str, addr: tuple, channels: []):
		self.sock = sock
		self.nick = nick
		self.realname = realname
		self.addr = addr
		self.channels = []
		self.func_names = {
			"PING": self.ping,
			"JOIN": self.join_channel,
			"WHO": self.who,
			"PRIVMSG": self.privmsg,
			"PART": self.leave_channel,
			"NICK": self.set_nick,
			"USER": self.set_realname
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
				print("\033[1;32m>>\033[0m", data)
			else:
				return False
		except BrokenPipeError: # thank u vincent
			return False
		except ConnectionResetError:
			return False
		return data


	# Sends message(s)/commmand(s) to client socket
	def send_msg(self, msg: str):
		msg = bytes((msg + ("\r\n" if msg[len(msg)-2:] != "\r\n" else "")).encode("utf-8"))
		print("\033[1;31m<<\033[0m", msg)
		self.sock.sendall(msg)


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

		self.send_msg(f":{self.nick}!{self.realname}@{IP} NICK {nick}")
		self.nick = nick
		
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

		return True
	

	# Adds new client to clients list and sends appropriate messaging
	def add(self):
		sockets_list.append(self.sock)
		clients_list.append(self)
		timeout = 5
		
		while timeout > 0 and (self.nick == "" or self.realname == ""):
			data = self.parse_data()
			if comm_contents(data.decode("utf-8"), "NICK"):
				if not self.set_nick(comm_contents(data.decode("utf-8"), "NICK")) and self.realname != "":
					return False
			if comm_contents(data.decode("utf-8"), "USER"):
				if not self.set_realname(comm_contents(data.decode("utf-8"), "USER")):
					return False
		

		self.send_msg(f":{SERVER_NAME} 001 {self.nick} :Yo, welcome to {server_name}.")
		self.send_msg(f":{SERVER_NAME} 002 {self.nick} :Your host is {SERVER_NAME}, running version {version}")
		self.send_msg(f":{SERVER_NAME} 003 {self.nick} :This server was created {create_time} {tz_name}")
		self.send_msg(f":{SERVER_NAME} 251 {self.nick} :There {f'are {len(clients_list)} users' if len(clients_list) != 1 else 'is 1 user'} on the server.")
		self.send_msg(f":{SERVER_NAME} 422 {self.nick} :{motd}")

		console_print(f"NEW USER '{self.nick}!{self.realname}'")
	

	# Adds client to a channel, creates one if it doesn't exist
	def join_channel(self, channel_name: str):
		if channel_name[0] != '#':
			self.send_msg(f":{SERVER_NAME} 403 {self.nick} {channel_name} :No such channel")
			return
		
		try:
			console_print(f"TRYING TO JOIN CHANNEL '{channel_name}'")
			channels_dict[channel_name].append(self)
		except KeyError:
			console_print(f"NOT FOUND, CREATING CHANNEL '{channel_name}'")
			channels_dict[channel_name] = [self]
		
		self.channels.append(channel_name)
		for chan_cl in channels_dict[channel_name]:
			chan_cl.send_msg(f":{self.nick}!{self.realname}@{IP} JOIN {channel_name}")

		self.send_msg(f":{SERVER_NAME} 331 {self.nick} {channel_name} :No topic") #TODO topics
		
		usr_list_msg = f":{SERVER_NAME} 353 {self.nick} = {channel_name} :"
		nick_buffer = ""
		for chan_cl in channels_dict[channel_name]:
			if len(nick_buffer) > 32:
				self.send_msg(usr_list_msg + nick_buffer)
				nick_buffer = ""
			nick_buffer += chan_cl.nick + " "
		if len(nick_buffer) > 0:
			self.send_msg(usr_list_msg + nick_buffer)
			
		self.send_msg(f":{SERVER_NAME} 366 {self.nick} {channel_name} :End of NAMES list")

		console_print(f"JOINED CHANNEL '{channel_name}'")
		
	
	# Responds to WHO command from the client, sends vebose list of clients in the channel
	def who(self, channel_name: str):
		for chan_cl in channels_dict[channel_name]:
			self.send_msg(f":{SERVER_NAME} 352 {self.nick} {channel_name} {self.realname} {self.addr[0]} {SERVER_NAME} {chan_cl.nick} H :0 {chan_cl.realname}")

		self.send_msg(f":{SERVER_NAME} 315 {self.nick} {channel_name} :End of WHO list")


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
					priv_cl.send_msg(f":{self.nick}!{self.realname}@{IP} PRIVMSG {target} :{msg}")
					return
			self.send_msg(f":{SERVER_NAME} 403 {self.nick} {target} :No such channel or user")

		else:
			for chan_cl in channels_dict[target]:
				if chan_cl.sock == self.sock:
					continue
				chan_cl.send_msg(f":{self.nick}!{self.realname}@{IP} PRIVMSG {target} :{msg}")


	# Removes client from channel
	def leave_channel(self, channel_and_comment: str):
		channel_name = channel_and_comment[:channel_and_comment.find(' ')]
		comment = channel_and_comment[channel_and_comment.find(':') + 1:] #TODO try to use comm_contents

		console_print(f"LEAVING CHANNEL {channel_name}")

		if channel_name[0] != '#':
			console_print(f"CANT FIND CHANNEL {channel_name}")
			self.send_msg(f":{SERVER_NAME} 403 {self.nick} {channel_name} :No such channel")
			return
		
		for chan_cl in channels_dict[channel_name]:
			chan_cl.send_msg(f":{self.nick}!{self.realname}@{IP} PART {channel_name} :{comment}")
		
		channels_dict[channel_name].remove(self)
		if len(channels_dict[channel_name]) == 0:
			console_print(f"NO USERS IN '{channel_name}', DELETING")
			del channels_dict[channel_name]
		self.channels.remove(channel_name)
			
	
	def ping(self, lag_str: str):
		self.send_msg(f":{SERVER_NAME} PONG {socket.getfqdn(self.addr[0])} :{lag_str}")


while True:
	read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

	for sock in read_sockets:
		if sock == serv_sock:
			cl_sock, cl_addr = serv_sock.accept()
			console_print(f"OPEN connection from {cl_addr}")
			new_cl = Client(cl_sock, "", "", cl_addr, [])
			new_cl.add()
			console_print(f"NUMBER OF CLIENTS: {len(clients_list)}")
		else:
			client = Client.find_client(sock)
			data = client.parse_data()

			if data is False or data.decode("utf-8").find("QUIT") == 0:
				console_print(f"CLOSE connection from {client.addr}")

				for chan_name in list(client.channels):
					client.comm_func("PART", f"{chan_name} :Leaving server")
				
				sockets_list.remove(sock)
				clients_list.remove(client)

				console_print(f"NUMBER OF CLIENTS: {len(clients_list)}")
			
			else:
				data_str = data.decode("utf-8")

				for func_key in client.func_names.keys():
					if comm_contents(data_str, func_key) and ((client.nick != "" and client.realname != "") or (func_key == "NICK" or func_key == "USER")):
						client.comm_func(func_key, comm_contents(data_str, func_key))
						break
