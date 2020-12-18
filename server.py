#!/bin/python3
"""
https://tools.ietf.org/html/rfc2810 - general architecture
https://tools.ietf.org/html/rfc2812 - client/server comms
https://docs.python.org/3.9/howto/sockets.html - python socket docs
https://medium.com/python-pandemonium/python-socket-communication-e10b39225a4c - tutorial 1
https://realpython.com/python-sockets/ - tutorial 2
https://ircv3.net/specs/core/capability-negotiation.html - stuff i found on CAP, the initial command, though most likely wont matter (mostly didnt)
https://stackoverflow.com/questions/5163255/regular-expression-to-match-irc-nickname - regex for nicks
--------------------------------------------------------------------------------
TODO: fix :: in QUIT
"""

import socket
from select import select
import string
from datetime import datetime
from pytz import reference
from utils import console_print, comm_contents

MOTD = "No MOTD set."
try:
	MOTD = "MOTD: " + open("motd.txt", "r").read()
except:
	pass

today = datetime.now()
CREATE_TIME = f"{today.strftime('%Y-%m-%d, %H:%M:%S')} {reference.LocalTimezone().tzname(today)}" # Time and timezone

HOST_NAME = "the-inn"
VERSION = "0.3"
SERVER_NAME = "Yulgar's Inn"
SERVER_IP = "localhost"
PORT = 6667

SERV_SOCK = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
SERV_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERV_SOCK.bind((SERVER_IP, PORT))
SERV_SOCK.listen(5)
SERV_SOCK.setblocking(False)

SOCKETS_LIST = [SERV_SOCK]
CLIENTS = set()
BOTS = set()
CHANNELS = {}

print("\033[1;36mServer started.")
print("Current time:", CREATE_TIME)
print(f"Listening on [{SERVER_IP}]:{PORT}\033[0m")


class Client:
	# Initialises Client
	def __init__(self, sock: socket.socket, nick: str, realname: str, addr: tuple, bot: bool = False, desc: str = ""):
		self.sock = sock
		self.nick = nick
		self.realname = realname
		self.addr = addr
		self.channel_names = set()
		self.bot = bot
		self.desc = desc
		self.func_names = {
			"PING": self.ping,
			"JOIN": self.join_channel,
			"WHO": self.who,
			"PRIVMSG": self.privmsg,
			"PART": self.leave_channel,
			"NICK": self.set_nick,
			"USER": self.set_realname,
			"SERVICE": self.service,
			"QUIT": self.leave_server
		}


	@staticmethod
	# Finds client by socket
	def find_client(query):
		if type(query) == socket.socket:
			for cl in CLIENTS:
				if cl.sock == query:
					return cl
		elif type(query) == str:
			for cl in CLIENTS:
				if cl.nick == query:
					return cl
		return None
	

	# Helper function. Checks if nickname or realname is valid
	def __checkname(self, what: str, name: str):
		if len(name) == 0 or len(name) > 9:
			console_print(f"REJECTED {what} (too short/long)")
			self.send_msg(f"{what} rejected. Length must be from 1 to 9 characters", "432")
			return False 

		allowed_symbols = "-_[]{}\\`|" + string.ascii_letters + string.digits

		try:
			for s in name:
				allowed_symbols.find(s)
		except ValueError:
			console_print(f"REJECTED {what} (invalid)")
			self.send_msg(f"{what} rejected. Only letters, digits and " + "-_[]{}\\`| are allowed", "432")
			return False 
	

	# Definitions of functions by IRC commands for easier usage in the main loop
	def comm_func(self, func: str, arg):
		return self.func_names[func](arg)
	

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
	def send_msg(self, msg: str, replycode: str = None, args: list = []):
		try:
			if replycode is not None:
				msg = f":{HOST_NAME} {replycode} {self.nick} {' '.join(args)} :{msg}"
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

		if self.__checkname("nick", nick) is False:
			return False
				
		for cl in CLIENTS:
			if cl.nick == nick and cl.sock != self.sock:
				console_print("REJECTED nick (already taken)")
				self.send_msg(f"Nick rejected. This one is already taken", "433")
				return False

		self.send_msg(f":{self.nick}!{self.realname}@{HOST_NAME} NICK {nick}")
		self.nick = nick
		self.__welcome()
		
		return True


	# Sets realname for the Client
	def set_realname(self, data_str: str):
		realname = data_str[data_str.rfind(":") + 1:]
		console_print(f"USER {realname}")

		if self.__checkname("realname", realname) is False:
			return False

		self.realname = realname
		self.__welcome()

		return True
	

	# Adds new client to clients list and sends appropriate messaging
	def add_client(self):
		SOCKETS_LIST.append(self.sock)
		CLIENTS.add(self)
	

	# Welcomes new user if nick and realname are valid
	def __welcome(self):
		if (self.bot or self.realname != "") and self.nick != "": 
			if self.bot: self.send_msg(f"You are service {self.nick}", "383")
			else: self.send_msg(f"Yo, welcome to {SERVER_NAME} {self.nick}!{self.realname}@{HOST_NAME}", "001")
			self.send_msg(f"Your host is {HOST_NAME}, running VERSION {VERSION}", "002")
			self.send_msg(f"This server was created {CREATE_TIME}", "003")
			self.send_msg(f"{HOST_NAME} {VERSION}", "004")
			bot_count = len(BOTS)
			cl_count = len(CLIENTS) - bot_count
			self.send_msg(f"There {f'are {cl_count} users' if cl_count != 1 else 'is 1 user'} and {f'{bot_count} services' if bot_count != 1 else '1 service'} on the server.", "251")
			self.send_msg(MOTD, "422")

			console_print(f"NEW {f'SERVICE {self.nick}' if self.bot else f'CLIENT {self.nick}!{self.realname}'}")
	

	# Adds client to a channel, creates one if it doesn't exist
	def join_channel(self, channel_name: str):
		allowed_symbols = "-_[]{}\\`|#&+!" + string.ascii_letters + string.digits
		if channel_name[0] != '#' or any(c not in allowed_symbols for c in channel_name) or len(channel_name) > 9:
			self.send_msg("No such channel", "403", [channel_name])
			return
		
		try:
			console_print(f"TRYING TO JOIN CHANNEL '{channel_name}'")
			CHANNELS[channel_name].append(self)
		except KeyError:
			console_print(f"NOT FOUND, CREATING CHANNEL '{channel_name}'")
			CHANNELS[channel_name] = [self]
		
		self.channel_names.add(channel_name)
		for chan_cl in CHANNELS[channel_name]:
			chan_cl.send_msg(f":{self.nick}!{self.realname}@{HOST_NAME} JOIN {channel_name}")

		self.send_msg("No topic", "331", [channel_name])
		
		nick_buffer = ""
		for chan_cl in CHANNELS[channel_name]:
			if len(nick_buffer) > 32:
				self.send_msg(nick_buffer, "353", [f"= {channel_name}"])
				nick_buffer = ""
			nick_buffer += chan_cl.nick + " "
		if len(nick_buffer) > 0:
			self.send_msg(nick_buffer, "353", [f"= {channel_name}"])
			
		self.send_msg("End of NAMES list", "366", [channel_name])

		console_print(f"JOINED CHANNEL '{channel_name}'")
		
	
	# Responds to WHO command from the client, sends vebose list of clients in the channel
	def who(self, channel_name: str):
		for chan_cl in CHANNELS[channel_name]:
			args = [channel_name, chan_cl.realname, HOST_NAME, HOST_NAME, chan_cl.nick, "H"]
			self.send_msg(f"0 {chan_cl.realname}", "352", args)

		self.send_msg("End of WHO list", "315", [channel_name])


	# Sends a message to a channel or another client
	def privmsg(self, target_and_msg: str, notice: bool = False):
		allowed_symbols = "-_[]{}\\`|" + string.ascii_letters + string.digits
		target = target_and_msg[:target_and_msg.find(' ')]
		msg = target_and_msg[target_and_msg.find(':') + 1:]

		if target == "":
			return

		if target[0] in "&+!#":
			if target not in self.channel_names or any(c not in allowed_symbols + "#&+!" for c in target):
				self.send_msg("No such channel", "403", [target])
				return
			for chan_cl in CHANNELS[target]:
				if chan_cl.sock == self.sock:
					continue
				chan_cl.send_msg(f":{self.nick}!{self.realname}@{HOST_NAME} PRIVMSG {target} :{msg}")
		else:
			recipient = self.find_client(target)
			if any(c not in allowed_symbols for c in target) or recipient not in CLIENTS:
				self.send_msg("No such user", "401", [target])
				return

			recipient.send_msg(f":{self.nick}!{self.realname}@{HOST_NAME} PRIVMSG {target} :{msg}")
			


	# Removes client from channel
	def leave_channel(self, channel_and_comment: str):
		channel_name = channel_and_comment[:channel_and_comment.find(' ')]
		comment = channel_and_comment[channel_and_comment.find(':') + 1:]

		console_print(f"LEAVING CHANNEL {channel_name}")

		if channel_name[0] not in '&+!#' or channel_name not in self.channel_names:
			console_print(f"CANT FIND CHANNEL {channel_name}")
			self.send_msg("No such channel", "403", [channel_name])
			return
		
		for chan_cl in CHANNELS[channel_name]:
			chan_cl.send_msg(f":{self.nick}!{self.realname}@{HOST_NAME} PART {channel_name} :{comment}")
		
		self.channel_names.remove(channel_name)
		CHANNELS[channel_name].remove(self)
		if len(CHANNELS[channel_name]) == 0:
			console_print(f"NO USERS IN '{channel_name}', DELETING")
			del CHANNELS[channel_name]
			
	
	# Responds to a ping from the client
	def ping(self, lag_str: str):
		self.send_msg(f":{HOST_NAME} PONG {socket.getfqdn(self.addr[0])} :{lag_str}")


	def service(self, params: str):
		nick = params[:params.find(" ")]
		desc = params[params.find(":") + 1:]

		if self.set_nick(nick):
			self.desc = desc
			BOTS.add(self)


	def leave_server(self, comment: str):
		console_print(f"CLOSE connection from {self.addr}")
		comment = comment[comment.find(":") + 1:]

		for chan_name in list(self.channel_names):
			self.comm_func("PART", f"{chan_name} :{comment}")
		
		self.send_msg(f":{self.nick}!{self.realname}@{HOST_NAME} QUIT :{comment}")
		
		SOCKETS_LIST.remove(self.sock)
		CLIENTS.remove(self)
		if self.bot:
			BOTS.remove(self)

		console_print(f"NUMBER OF CLIENTS: {len(CLIENTS)}")


while True:
	read_sockets, _, exception_sockets = select(SOCKETS_LIST, [], SOCKETS_LIST)

	for sock in read_sockets:
		if sock == SERV_SOCK:
			cl_sock, cl_addr = SERV_SOCK.accept()
			console_print(f"OPEN connection from {cl_addr}")
			new_cl = Client(cl_sock, "", "", cl_addr, [], False)
			new_cl.add_client()
			console_print(f"NUMBER OF CLIENTS: {len(CLIENTS)}")
		else:
			client = Client.find_client(sock)
			if client is None: continue

			data = client.parse_data()

			if data is False:
				client.leave_server(":Leaving server")
			
			else:
				for line in data.decode("utf-8").splitlines():
					for func_key in client.func_names.keys():
						if comm_contents(line, func_key) and ((client.nick != "" and client.realname != "") or (func_key == "NICK" or func_key == "USER")):
							client.comm_func(func_key, comm_contents(line, func_key))
							break
