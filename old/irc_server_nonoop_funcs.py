# def parse_sock(cl_sock: socket.socket) -> bytes:
# 	try:
# 		data = cl_sock.recv(2 ** 20)
# 		if len(data) != 0:
# 			print("\033[1;32m>>\033[0m", data)
# 		else:
# 			return False
# 	except BrokenPipeError: # thank u vincent
# 		return False
# 	except ConnectionResetError:
# 		return False
# 	return data


# def send_msg(cl_sock: socket.socket, msg: str):
# 	msg = bytes((msg + ("\r\n" if msg[len(msg)-2:] != "\r\n" else "")).encode("utf-8"))
# 	print("\033[1;31m<<\033[0m", msg)
# 	cl_sock.sendall(msg)


# def set_nick(cl_sock: socket.socket, data_str: str):
# 	nick = data_str
# 	console_print(f"NICK {nick}")

# 	rejected_symbols = "\"`'!/\\%+-*#@$&;:,.\r\n\t [](){}"
# 	for s in rejected_symbols:
# 		if nick.find(s) != -1:
# 			console_print(f"REJECTED nick (has any of: [!:@ *;#\"`'/\\%+-.\\r\\n\\t$,&])")
# 			send_msg(cl_sock, "nick rejected. (has any of: [!:@ *;#\"`'/\\%+-.\\r\\n\\t$,&])\r\nPlease pick a different nick without any of those symbols.")
# 			return

# 	for cl in clients:
# 		if clients[cl]['nick'] == nick:
# 			console_print(f"REJECTED nick (already taken)")
# 			send_msg(cl_sock, f"nick rejected. (already taken)\r\nPlease pick a different nick")
# 			return

# 	# :tadz_!arsic@::1 NICK tadz
# 	send_msg(cl_sock, f":{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}@{IP} NICK {nick}")
# 	clients[cl_sock]['nick'] = nick


# def set_realname(cl_sock: socket.socket, data_str: str):
# 	print(data_str)
# 	realname = data_str[data_str.find(":") + 1:]
# 	console_print(f"USER {realname}")

# 	rejected_symbols = "\"`'!/%+*#@$&;:,.\r\n\t ()"
# 	for s in rejected_symbols:
# 		if realname.find(s) != -1:
# 			console_print(f"REJECTED realname (has any of: [\"`'!/%+*#@$&;:,.\\r\\n\\t<space>()])")
# 			send_msg(cl_sock, "realname rejected. (has any of: [\"`'!/%+*#@$&;:,.\\r\\n\\t<space>()])\r\nPlease reconnect with a different realname without any of those symbols.")
# 			return

# 	clients[cl_sock]['realname'] = realname


# def new_client(cl_sock: socket.socket, cl_addr: tuple):
# 	sockets_list.append(cl_sock)
# 	clients[cl_sock] = {
# 		'nick': "",
# 		'realname': "",
# 		'ip': cl_sock.getpeername()[0],
# 		'channels': []
# 	}
	
# 	while clients[cl_sock]['nick'] == "" or clients[cl_sock]['realname'] == "":
# 		data = parse_sock(cl_sock)
# 		if data is False:
# 			console_print(f"FAILED connection from {cl_addr}")
# 			return

# 		if clients[cl_sock]['nick'] == "" and comm_contents(data.decode("utf-8"), "NICK"):
# 			set_nick(cl_sock, comm_contents(data.decode("utf-8"), "NICK"))
# 		if clients[cl_sock]['realname'] == "" and comm_contents(data.decode("utf-8"), "USER"):
# 			set_realname(cl_sock, comm_contents(data.decode("utf-8"), "USER"))

# 	send_msg(cl_sock, f":{hostname} 001 {clients[cl_sock]['nick']} :Yo, welcome to {server_name}.")
# 	send_msg(cl_sock, f":{hostname} 002 {clients[cl_sock]['nick']} :Your host is {hostname}, running version {version}")
# 	send_msg(cl_sock, f":{hostname} 003 {clients[cl_sock]['nick']} :This server was created {create_time} {tz_name}")
# 	send_msg(cl_sock, f":{hostname} 251 {clients[cl_sock]['nick']} :There {f'are {len(clients)} users' if len(clients) != 1 else 'is 1 user'} on the server.")
# 	send_msg(cl_sock, f":{hostname} 422 {clients[cl_sock]['nick']} :{motd}")

# 	console_print(f"NEW USER '{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}'")


# def join_channel(cl_sock: socket.socket, channel_name: str):
# 	if channel_name[0] != '#':
# 		send_msg(cl_sock, f":{hostname} 403 {clients[cl_sock]['nick']} {channel_name} :No such channel")
# 		return
	
# 	try:
# 		console_print(f"TRYING TO JOIN CHANNEL '{channel_name}'")
# 		channels[channel_name].append(cl_sock)
# 	except KeyError:
# 		console_print(f"NOT FOUND, CREATING CHANNEL '{channel_name}'")
# 		channels[channel_name] = [cl_sock]
	
# 	clients[cl_sock]['channels'].append(channel_name)
# 	for chan_sock in channels[channel_name]:
# 		send_msg(chan_sock, f":{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}@{IP} JOIN {channel_name}")

# 	send_msg(cl_sock, f":{hostname} 331 {clients[cl_sock]['nick']} {channel_name} :No topic")
	
# 	usr_list_msg = f":{hostname} 353 {clients[cl_sock]['nick']} = {channel_name} :"
# 	nick_buffer = ""
# 	for chan_sock in channels[channel_name]:
# 		if len(nick_buffer) > 32:
# 			send_msg(cl_sock, usr_list_msg + nick_buffer)
# 			nick_buffer = ""
# 		nick_buffer += clients[chan_sock]['nick'] + " "
# 	if len(nick_buffer) > 0:
# 		send_msg(cl_sock, usr_list_msg + nick_buffer)
		
# 	send_msg(cl_sock, f":{hostname} 366 {clients[cl_sock]['nick']} {channel_name} :End of NAMES list")

# 	console_print(f"JOINED CHANNEL '{channel_name}'")


# def who(cl_sock: socket.socket, channel_name: str):

# 	for chan_sock in channels[channel_name]:
# 		send_msg(cl_sock, f":{hostname} 352 {clients[cl_sock]['nick']} {channel_name} {clients[chan_sock]['realname']} {IP} {hostname} {clients[chan_sock]['nick']} H :0 {clients[chan_sock]['realname']}")

# 	send_msg(cl_sock, f":{hostname} 315 {clients[cl_sock]['nick']} {channel_name} :End of WHO list")


# def privmsg(cl_sock: socket.socket, dest_and_msg: str):
# 	dest = dest_and_msg[:dest_and_msg.find(' ')]
# 	msg = dest_and_msg[dest_and_msg.find(':') + 1:]

# 	if len(bytes(msg.encode("utf-8"))) > (2 ** 10):
# 		send_msg(cl_sock, "No spammerino")
# 		return

# 	if dest[0] != '#':
# 		for priv_sock in clients.keys():
# 			if clients[priv_sock]['nick'] == dest:
# 				send_msg(priv_sock, f":{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}@{IP} PRIVMSG {dest} :{msg}")
# 				return
# 		send_msg(cl_sock, f":{SERVER_NAME} 403 {clients[cl_sock]['nick']} {dest} :No such channel or user")

# 	else:
# 		for chan_sock in channels[dest]:
# 			if chan_sock == cl_sock:
# 				continue
# 			send_msg(chan_sock, f":{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}@{IP} PRIVMSG {dest} :{msg}")
# 		# >> :tadz!arsic@::1 PRIVMSG #test :XDDDDD


# def leave_channel(cl_sock: socket.socket, channel_and_comment: str):
# 	channel_name = channel_and_comment[:channel_and_comment.find(' ')]
# 	comment = channel_and_comment[channel_and_comment.find(':') + 1:]

# 	console_print(f"LEAVING CHANNEL {channel_name}")

# 	if channel_name[0] != '#':
# 		console_print(f"CANT FIND CHANNEL {channel_name}")
# 		send_msg(cl_sock, f":{SERVER_NAME} 403 {clients[cl_sock]['nick']} {channel_name} :No such channel")
# 		return
	
# 	for chan_sock in channels[channel_name]:
# 		send_msg(chan_sock, f":{clients[cl_sock]['nick']}!{clients[cl_sock]['realname']}@{IP} PART {channel_name} :{comment}")
	
# 	channels[channel_name].remove(cl_sock)
# 	if len(channels[channel_name]) == 0:
# 		console_print(f"NO USERS IN '{channel_name}', DELETING")
# 		del channels[channel_name]
# 	clients[cl_sock]['channels'].remove(channel_name)

# def ping(cl_sock: socket.socket, lag_str: str):
# 	send_msg(cl_sock, f":{SERVER_NAME} PONG {socket.getfqdn(clients[cl_sock]['ip'])} :{lag_str}")