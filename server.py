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
"""

import sys, socket, string
from threading import Thread, Semaphore
from datetime import datetime
from pytz import reference
from utils import consolePrint, commContents

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
SERVER_IP = "::"
PORT = 6667

SERV_SOCK = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
SERV_SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERV_SOCK.bind((SERVER_IP, PORT))

SOCKETS = [SERV_SOCK]
CLIENTS = []
BOTS = []
CHANNELS = {}

ALLOWED_NAME_CHARS = "-_[]{}\\`|" + string.ascii_letters + string.digits
ALLOWED_CHAN_CHARS = ALLOWED_NAME_CHARS + "#&+!"

SEM = Semaphore()

print("\033[1;36mServer started.")
print("Current time:", CREATE_TIME)
print(f"Listening on [{SERVER_IP}]:{PORT}\033[0m")


class Client:
	# Initialise the Client class
	def __init__(self, sock: socket.socket, nick: str, realname: str, ip: str):
		self.sock = sock
		self.nick = nick
		self.realname = realname
		self.ip = ip
		self.channel_names = set()
		self.welcome_done = False
		self.bot = False
		self.bot_desc = ""
		self.func_names = {
			"PING": self.pongClient,
			"JOIN": self.joinChannel,
			"WHO": self.whoChannel,
			"PRIVMSG": self.privmsgTarget,
			"PART": self.partChannel,
			"NICK": self.setNick,
			"USER": self.setRealname,
			"SERVICE": self.serviceClient,
			"QUIT": self.quitServer
		}

		self.__run()


	@staticmethod
	# Find client by nick, returns None if not found
	def findClient(nick: str):
		for cl in CLIENTS:
			if cl.nick == nick:
				return cl
		return None
	

	# Run thread, listen to socket
	def __run(self):
		self.__addClient()
		while True:
			data = self.__parseData()

			SEM.acquire()
			if data is None:
				self.__commFunc("QUIT", ":Disconnected")
				return
			
			for line in data.decode("utf-8").split("\r\n"):
				comm = line[:line.find(' ')] if line.find(' ') != -1 else line
				is_valid_client = self.nick != "" and (self.realname != "" or self.bot)
				is_name_comm = comm in ["NICK", "USER", "SERVICE"]

				if commContents(line, comm) and (is_valid_client or is_name_comm):
					self.__commFunc(comm, commContents(line, comm))
					if comm == "QUIT":
						SEM.release()
						return
			SEM.release()
	

	# Add new socket and client to lists
	def __addClient(self):
		SOCKETS.append(self.sock)
		CLIENTS.append(self)
		consolePrint(f"USER COUNT: {len(CLIENTS) - len(BOTS)}, BOT COUNT: {len(BOTS)}")
	

	# Receive and parse message(s)/command(s) from client socket
	def __parseData(self) -> bytes:
		try:
			data = self.sock.recv(2 ** 20)
			if len(data) != 0:
				print("\033[1;32m>>\033[0m", f"\033[37m{data}\033[0m")
				return data
			else:
				return None
		except BrokenPipeError:
			return None
		except ConnectionResetError:
			return None
	

	# Send message(s)/commmand(s) to client socket
	def __sendMsg(self, msg: str, replycode: str = None, args: list = []):
		try:
			if replycode is not None:
				args = list(args)
				if len(args) == 0 or args[0] != self.nick:
					args.insert(0, self.nick)
				msg = f":{HOST_NAME} {replycode} {' '.join(args)} :{msg}"

			msg = bytes((msg + ("\r\n" if msg[len(msg)-2:] != "\r\n" else "")).encode("utf-8"))
			print("\033[1;31m<<\033[0m", f"\033[37m{msg}\033[0m")
			self.sock.sendall(msg)

		except BrokenPipeError:
			consolePrint("FAILED TO SEND")
		except ConnectionResetError:
			consolePrint("FAILED TO SEND")
		except:
			consolePrint("UNEXPECTED ERROR")

	
	# Return function by IRC command name for ease of use
	def __commFunc(self, func: str, arg):
		if func in self.func_names.keys():
			return self.func_names[func](arg)
		else: return False
	

	# Check if nickname or realname is valid
	def __validName(self, what: str, name: str):
		error = ""
		if not 0<len(name)<=9:
			error += "Length must be from 1 to 9 characters. "

		if any(c not in ALLOWED_NAME_CHARS for c in name):
			error += "Only letters, digits and -_[]{}\\`| are allowed."
		
		if error != "":
			consolePrint(f"REJECTED {what}. {error}")
			self.__sendMsg(f"{what} rejected. {error}", "432")
			return False

		return True
	

	# Welcome new user if nick and realname are valid or if nick is valid and the client is a bot
	def __welcomeClient(self):
		if not self.welcome_done and (self.bot or self.realname != "") and self.nick != "": 
			if self.bot: 
				self.__sendMsg(f"You are service {self.nick}", "383")
			else: 
				self.__sendMsg(f"Yo, welcome to {SERVER_NAME} {self.nick}!{self.realname}@{HOST_NAME}", "001")

			# client and bot counts; string formatting in accordance to counts
			bot_count = len(BOTS)
			cl_count = len(CLIENTS) - bot_count
			cl_count_str = f'are {cl_count} users' if cl_count != 1 else 'is 1 user'
			bot_count_str = f'{bot_count} services' if bot_count != 1 else '1 service'

			self.__sendMsg(f"Your host is {HOST_NAME}, running version {VERSION}", "002")
			self.__sendMsg(f"This server was created {CREATE_TIME}", "003")
			self.__sendMsg(f"{HOST_NAME} {VERSION}", "004")
			self.__sendMsg(f"There {cl_count_str} and {bot_count_str} on the server.", "251")
			self.__sendMsg(MOTD, "422")

			# make sure the welcome message is sent only once
			self.welcome_done = True

			consolePrint(f"NEW {f'SERVICE {self.nick}' if self.bot else f'CLIENT {self.nick}!{self.realname}'}")
	

	# Send names list
	def __sendNamesList(self, chan_name: str):
		# limit names list response to no more than 40 characters per line for better log readability
		nick_buffer = ""
		for chan_cl in CHANNELS[chan_name]:
			nick_buffer += chan_cl.nick + " "
			if len(nick_buffer) >= 32:
				self.__sendMsg(nick_buffer[:-1], "353", [f"= {chan_name}"])
				nick_buffer = ""
		if len(nick_buffer) > 0:
			self.__sendMsg(nick_buffer[:-1], "353", [f"= {chan_name}"])
			
		self.__sendMsg("End of NAMES list", "366", [chan_name])


	# Set nick for the Client
	def setNick(self, nick: str):
		consolePrint(f"NICK {nick}")

		if not self.__validName("nick", nick):
			return False

		# checks if nick is taken
		found_client = self.findClient(nick)
		if found_client is not None and found_client.sock != self.sock:
			consolePrint("REJECTED nick (already taken)")
			self.__sendMsg(f"Nick rejected. This one is already taken", "433")
			return False

		self.__sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} NICK {nick}")
		self.nick = nick
		self.__welcomeClient()
		
		return True


	# Set realname for the Client
	def setRealname(self, data_str: str):
		realname = data_str[data_str.rfind(":") + 1:]
		consolePrint(f"USER {realname}")

		if not self.__validName("realname", realname):
			return False

		self.realname = realname
		self.__welcomeClient()

		return True
	

	# Add client to a channel, create one if it doesn't exist
	def joinChannel(self, chan_name: str):
		if chan_name[0] not in "&+!#" or any(c not in ALLOWED_CHAN_CHARS for c in chan_name) or len(chan_name) > 9:
			self.__sendMsg("Bad channel name. Only letters, digits and -_[]{}\\`|&+!# allowed.\n" +
				"It Must also start with any of &+!#.", "403", [chan_name])
			return
		
		# if channel exists, add client; if not, create channel with client
		consolePrint(f"{self.nick} TRYING TO JOIN CHANNEL {chan_name}")
		if chan_name in CHANNELS.keys():
			CHANNELS[chan_name].append(self)
		else:
			consolePrint(f"CREATING CHANNEL {chan_name}")
			CHANNELS[chan_name] = [self]
		self.channel_names.add(chan_name) # update the client's channel list

		# announce in the channel that the client has joined
		for chan_cl in CHANNELS[chan_name]:
			chan_cl.__sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} JOIN {chan_name}")

		self.__sendMsg("No topic", "331", [chan_name]) #TODO: channel topics
		self.__sendNamesList(chan_name)
		consolePrint(f"JOINED CHANNEL {chan_name}")
		
	
	# Send verbose list of clients in the channel
	def whoChannel(self, chan_name: str):
		for chan_cl in CHANNELS[chan_name]:
			args = [chan_name, chan_cl.realname, HOST_NAME, HOST_NAME, chan_cl.nick, "H"]
			self.__sendMsg(f"0 {chan_cl.realname}", "352", args)

		self.__sendMsg("End of WHO list", "315", [chan_name])


	# Send a message to a channel or another client
	def privmsgTarget(self, target_and_msg: str, notice: bool = False):
		target = target_and_msg[:target_and_msg.find(' ')]
		msg = target_and_msg[target_and_msg.find(':') + 1:]

		if target == "":
			return

		if target[0] in "&+!#":
			if target not in self.channel_names or any(c not in ALLOWED_CHAN_CHARS for c in target):
				self.__sendMsg("No such channel", "403", [target])
				return
			for chan_cl in CHANNELS[target]:
				if chan_cl.sock == self.sock:
					continue
				chan_cl.__sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} PRIVMSG {target} :{msg}")
		else:
			recipient = self.findClient(target)
			if any(c not in ALLOWED_NAME_CHARS for c in target) or recipient not in CLIENTS:
				self.__sendMsg("No such user", "401", [target])
				return
			# if recipient.sock == self.sock:
			# 	return
			# yes, you can message yourself. this is intentional, not everyone has friends :(
			
			recipient.__sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} PRIVMSG {target} :{msg}")
			

	# Remove client from channel
	def partChannel(self, channel_and_comment: str):
		chan_name = channel_and_comment[:channel_and_comment.find(' ')]
		comment = channel_and_comment[channel_and_comment.find(':') + 1:]

		consolePrint(f"{self.nick} LEAVING CHANNEL {chan_name}")

		if chan_name not in self.channel_names:
			consolePrint(f"CANT FIND CHANNEL {chan_name}")
			self.__sendMsg("No such channel", "403", [chan_name])
			return
		
		# announce in the channel that the client has left
		for chan_cl in CHANNELS[chan_name]:
			chan_cl.__sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} PART {chan_name} :{comment}")
		
		# clean up appropriate datasets
		self.channel_names.remove(chan_name)
		CHANNELS[chan_name].remove(self)
		if len(CHANNELS[chan_name]) == 0:
			consolePrint(f"NO CLIENTS IN {chan_name}, DELETING")
			del CHANNELS[chan_name]
			
	
	# Respond to a ping from the client
	def pongClient(self, lag_str: str):
		self.__sendMsg(f":{HOST_NAME} PONG {self.ip} :{lag_str}")


	# Set client as service/bot
	def serviceClient(self, params: str):
		nick = params[:params.find(" ")]
		desc = params[params.find(":") + 1:]

		if self.setNick(nick):
			self.bot_desc = desc
			self.bot = True
			BOTS.append(self)
			self.__welcomeClient()


	def quitServer(self, comment: str = ":Leaving"):
		consolePrint(f"CLOSE connection from {self.ip}")
		comment = comment[comment.find(":") + 1:]

		# leave channels
		for chan_name in list(self.channel_names):
			self.__commFunc("PART", f"{chan_name} :{comment}")
		
		self.__sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} QUIT :{comment}")
		
		# clean up appropriate datasets
		SOCKETS.remove(self.sock)
		CLIENTS.remove(self)
		if self.bot:
			BOTS.remove(self)

		consolePrint(f"USER COUNT: {len(CLIENTS) - len(BOTS)}, BOT COUNT: {len(BOTS)}")



if __name__ == "__main__":
	# Main loop
	while True:
		SERV_SOCK.listen(5)
		cl_sock, cl_addr = SERV_SOCK.accept()

		consolePrint(f"OPEN connection from {socket.getfqdn(cl_addr[0])}")
		Thread(target=Client, args=[cl_sock, "", "", socket.getfqdn(cl_addr[0])]).start()