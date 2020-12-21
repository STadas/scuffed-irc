#!/bin/python3
"""
https://tools.ietf.org/html/rfc2810 - general architecture
https://tools.ietf.org/html/rfc2812 - client/server comms
https://docs.python.org/3.9/howto/sockets.html - python socket docs
https://medium.com/python-pandemonium/python-socket-communication-e10b39225a4c - tutorial 1
https://realpython.com/python-sockets/ - tutorial 2
https://www.youtube.com/watch?v=Lbfe3-v7yE0&list=PLQVvvaa0QuDdzLB_0JSTTcl8E8jsJLhR5 - tutorial videos playlist
https://ircv3.net/specs/core/capability-negotiation.html - stuff i found on CAP, the initial command, though most likely wont matter (mostly didnt)
https://stackoverflow.com/questions/5163255/regular-expression-to-match-irc-nickname - regex for nicks
--------------------------------------------------------------------------------
"""

import sys, socket, string
from threading import Thread, Semaphore
from datetime import datetime
from pytz import reference
from serverutils import consolePrint, commContents, parseArgs


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

		self.run()
	

	# Run thread, listen to socket
	def run(self):
		self.addClient()
		while True:
			data = self.parseData()

			SEM.acquire()
			if data is None:
				self.commFunc("QUIT", ":Disconnected")
				return
			
			for line in data.decode("utf-8").split("\r\n"):
				comm = line[:line.find(' ')] if line.find(' ') != -1 else line
				is_valid_client = self.nick != "" and (self.realname != "" or self.bot)
				is_name_comm = comm in ["NICK", "USER", "SERVICE"]
				comm_contents = commContents(line, comm)

				if comm_contents and (is_valid_client or is_name_comm):
					self.commFunc(comm, comm_contents)
					if comm == "QUIT":
						SEM.release()
						return
			SEM.release()
	

	# Add new socket and client to lists
	def addClient(self):
		SOCKETS.append(self.sock)
		CLIENTS.append(self)
		consolePrint(f"USER COUNT: {len(CLIENTS) - len(BOTS)}, BOT COUNT: {len(BOTS)}")
	

	# Receive and parse message(s)/command(s) from client socket
	def parseData(self) -> bytes:
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
	def sendMsg(self, msg: str, reply_code: str = None, msg_args: list = []):
		try:
			if reply_code is not None:
				msg_args = list(msg_args)
				if len(msg_args) == 0 or msg_args[0] != self.nick:
					msg_args.insert(0, self.nick)
				msg = f":{HOST_NAME} {reply_code} {' '.join(msg_args)} :{msg}"

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
	def commFunc(self, func: str, arg):
		if func in self.func_names.keys():
			return self.func_names[func](arg)
		else: return False
	

	# Find client by nick, returns None if not found
	@staticmethod
	def findClient(nick: str):
		for cl in CLIENTS:
			if cl.nick == nick:
				return cl
		return None
	

	# Check if nickname or realname is valid
	def validName(self, type: str, name: str):
		error = ""
		if not 0<len(name)<=9:
			error += "Length must be from 1 to 9 characters. "

		if any(c not in ALLOWED_NAME_CHARS for c in name):
			error += "Only letters, digits and -_[]{}\\`| are allowed."
		
		if type == "nick":
			# checks if nick is taken
			found_client = self.findClient(name)
			if found_client is not None and found_client.sock != self.sock:
				consolePrint("REJECTED nick (already taken)")
				self.sendMsg(f"Nick rejected. This one is already taken", "433")	
		
		if error != "":
			consolePrint(f"REJECTED {type}. {error}")
			self.sendMsg(f"{type} rejected. {error}", "432")
			return False

		return True
	

	# Welcome new user if nick and realname are valid or if nick is valid and the client is a bot
	def welcomeClient(self):
		if not self.welcome_done and (self.bot or self.realname != "") and self.nick != "": 
			if self.bot: 
				self.sendMsg(f"You are service {self.nick}", "383")
			else: 
				self.sendMsg(f"Hello, welcome to {SERVER_NAME} {self.nick}!{self.realname}@{HOST_NAME}", "001")

			# client and bot counts; string formatting in accordance to counts
			bot_count = len(BOTS)
			cl_count = len(CLIENTS) - bot_count
			cl_count_str = f'are {cl_count} users' if cl_count != 1 else 'is 1 user'
			bot_count_str = f'{bot_count} services' if bot_count != 1 else '1 service'

			self.sendMsg(f"Your host is {HOST_NAME}, running version {VERSION}", "002")
			self.sendMsg(f"This server was created {CREATE_TIME}", "003")
			self.sendMsg(f"{HOST_NAME} {VERSION}", "004")
			self.sendMsg(f"There {cl_count_str} and {bot_count_str} on the server.", "251")
			self.sendMsg(MOTD, "422")

			# make sure the welcome message is sent only once
			self.welcome_done = True

			consolePrint(f"NEW {f'SERVICE {self.nick}' if self.bot else f'CLIENT {self.nick}!{self.realname}'}")
	

	# Send names list
	def sendNamesList(self, chan_name: str):
		# limit names list response to no more than 40 characters per line for better log readability
		nick_buffer = ""
		for chan_cl in CHANNELS[chan_name]:
			nick_buffer += chan_cl.nick + " "
			if len(nick_buffer) >= 32:
				self.sendMsg(nick_buffer[:-1], "353", [f"= {chan_name}"])
				nick_buffer = ""
		if len(nick_buffer) > 0:
			self.sendMsg(nick_buffer[:-1], "353", [f"= {chan_name}"])
			
		self.sendMsg("End of NAMES list", "366", [chan_name])


	# ========= MAIN RESPONSE FUNCTIONS =========


	# Set nick for the Client
	def setNick(self, nick: str):
		consolePrint(f"NICK {nick}")

		if not self.validName("nick", nick):
			return False

		self.sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} NICK {nick}")
		self.nick = nick
		self.welcomeClient()
		
		return True


	# Set realname for the Client
	def setRealname(self, data_str: str):
		realname = data_str[data_str.rfind(":") + 1:]
		consolePrint(f"USER {realname}")

		if not self.validName("realname", realname):
			return False

		self.realname = realname
		self.welcomeClient()

		return True
	

	# Add client to a channel, create one if it doesn't exist
	def joinChannel(self, chan_name: str):
		if chan_name[0] not in "&+!#" or any(c not in ALLOWED_CHAN_CHARS for c in chan_name) or len(chan_name) > 9:
			self.sendMsg("Bad channel name. Only letters, digits and -_[]{}\\`|&+!# allowed.\n" +
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
			chan_cl.sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} JOIN {chan_name}")

		self.sendMsg("No topic", "331", [chan_name]) #TODO: channel topics
		self.sendNamesList(chan_name)
		consolePrint(f"JOINED CHANNEL {chan_name}")
		
	
	# Send verbose list of clients in the channel
	def whoChannel(self, chan_name: str):
		for chan_cl in CHANNELS[chan_name]:
			msg_args = [chan_name, chan_cl.realname, HOST_NAME, HOST_NAME, chan_cl.nick, "H"]
			self.sendMsg(f"0 {chan_cl.realname}", "352", msg_args)

		self.sendMsg("End of WHO list", "315", [chan_name])


	# Send a message to a channel or another client
	def privmsgTarget(self, target_and_msg: str, notice: bool = False):
		target = target_and_msg[:target_and_msg.find(' ')]
		msg = target_and_msg[target_and_msg.find(':') + 1:]

		if target == "":
			return

		if target[0] in "&+!#":
			if target not in self.channel_names or any(c not in ALLOWED_CHAN_CHARS for c in target):
				self.sendMsg("No such channel", "403", [target])
				return
			for chan_cl in CHANNELS[target]:
				if chan_cl.sock == self.sock:
					continue
				chan_cl.sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} PRIVMSG {target} :{msg}")
		else:
			recipient = self.findClient(target)
			if any(c not in ALLOWED_NAME_CHARS for c in target) or recipient not in CLIENTS:
				self.sendMsg("No such user", "401", [target])
				return
			# if recipient.sock == self.sock:
			# 	return

			# yes, you can message yourself. This is intentional, not everyone has friends :(
			
			recipient.sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} PRIVMSG {target} :{msg}")
			

	# Remove client from channel
	def partChannel(self, channel_and_comment: str):
		chan_name = channel_and_comment[:channel_and_comment.find(' ')]
		comment = channel_and_comment[channel_and_comment.find(':') + 1:]

		consolePrint(f"{self.nick} LEAVING CHANNEL {chan_name}")

		if chan_name not in self.channel_names:
			consolePrint(f"CANT FIND CHANNEL {chan_name}")
			self.sendMsg("No such channel", "403", [chan_name])
			return
		
		# announce in the channel that the client has left
		for chan_cl in CHANNELS[chan_name]:
			chan_cl.sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} PART {chan_name} :{comment}")
		
		# clean up appropriate datasets
		self.channel_names.remove(chan_name)
		CHANNELS[chan_name].remove(self)
		if len(CHANNELS[chan_name]) == 0:
			consolePrint(f"NO CLIENTS IN {chan_name}, DELETING")
			del CHANNELS[chan_name]
			
	
	# Respond to a ping from the client
	def pongClient(self, lag_str: str):
		self.sendMsg(f":{HOST_NAME} PONG {self.ip} :{lag_str}")


	# Set client as service/bot
	def serviceClient(self, params: str):
		nick = params[:params.find(" ")]
		desc = params[params.find(":") + 1:]

		if self.setNick(nick):
			self.bot_desc = desc
			self.bot = True
			BOTS.append(self)
			self.welcomeClient()


	def quitServer(self, comment: str = ":Leaving"):
		consolePrint(f"CLOSE connection from {self.ip}")
		comment = comment[comment.find(":") + 1:]

		# leave channels
		for chan_name in list(self.channel_names):
			self.commFunc("PART", f"{chan_name} :{comment}")
		
		self.sendMsg(f":{self.nick}!{self.realname}@{HOST_NAME} QUIT :{comment}")
		
		# clean up appropriate datasets
		SOCKETS.remove(self.sock)
		CLIENTS.remove(self)
		if self.bot:
			BOTS.remove(self)

		consolePrint(f"USER COUNT: {len(CLIENTS) - len(BOTS)}, BOT COUNT: {len(BOTS)}")
	

def handleArgs(args: dict):
	global MOTD, MOTD_FILE, HOST_NAME, SERVER_NAME, SERVER_IP, PORT
	keys = args.keys()
	if "motd" in keys:
		MOTD = "MOTD: " + args["motd"]
	if "motdfile" in keys:
		MOTD_FILE = args["motdfile"]
	if "hostname" in keys:
		HOST_NAME = args["hostname"]
	if "servername" in keys:
		SERVER_NAME = args["servername"]
	if "ip" in keys:
		SERVER_IP = args["ip"]
	if "port" in keys:
		PORT = args["port"]
	
	try:
		if "motd" not in keys or "motdfile" in keys:
			MOTD = "MOTD: " + open(MOTD_FILE, "r").read()
	except:
		pass


if __name__ == "__main__":
	# Time and timezone
	today = datetime.now()
	CREATE_TIME = f"{today.strftime('%Y-%m-%d, %H:%M:%S')} {reference.LocalTimezone().tzname(today)}"
	
	VERSION = "0.3"

	MOTD = "No MOTD set."
	MOTD_FILE = "motd.txt"
	HOST_NAME = socket.gethostname()
	SERVER_NAME = HOST_NAME + "'s server"
	SERVER_IP = "::"
	PORT = 6667

	args = parseArgs(sys.argv)
	if args == 1:
		sys.exit(args)
		quit()
	elif isinstance(args, dict):
		handleArgs(args)

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

	print("\033[1;36mStart time:", CREATE_TIME)
	print("Server started.")
	print(f"Listening on [{SERVER_IP}]:{PORT}\033[0m")

	# Main loop
	while True:
		SERV_SOCK.listen(5)
		cl_sock, cl_addr = SERV_SOCK.accept()

		consolePrint(f"OPEN connection from {socket.getfqdn(cl_addr[0])}")
		Thread(target=Client, args=[cl_sock, "", "", socket.getfqdn(cl_addr[0])]).start()