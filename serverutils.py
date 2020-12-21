def consolePrint(msg: str):
	print("\033[1;33m////\033[0m", msg)


def commContents(data_str: str, comm_str: str, to_str: str = '\r') -> str:
	# if data_str.find(comm_str) == -1:
	# 	return False
	
	comm_index = data_str.find(comm_str)
	if comm_index != 0 or len(comm_str) + 1 > len(data_str):
		return False
	
	from_index = len(comm_str) + 1

	find_to = data_str.find(to_str, from_index)
	find_r = data_str.find('\r', from_index)
	find_n = data_str.find ('\n', from_index)

	to_index = find_to if find_to != -1 else (find_r if find_r != -1 else (find_n if find_n != -1 else len(data_str)-1))

	return data_str[from_index:to_index + 1]


def parseArgs(args):
	help_msg =(
		"--- AVAILABLE FLAGS ---\n"
		"-help - displays this help message\n"
		"-motd - sets motd to provided string\n"
		"-motdfile - sets MOTD file to read from (overrides -motd if specified file exists)\n"
		"-hostname - sets hostname to use\n"
		"-servername - sets server name to use\n"
		"-ip - sets IP to use\n"
		"-port - sets port to listen to\n\n"
		"--- DEFAULTS ---\n"
		"motd: 'No MOTD set.'\n"
		"motdfile: 'motd.txt'\n"
		"hostname: your device's hostname\n"
		"servername: <hostname>'s server\n"
		"ip: '::', which is any IPv6 of your device in the local network (e.g. '::1', '', 'localhost'...)\n"
		"port: 6667\n\n"
		"--- EXAMPLES ---\n"
		"python3 server.py\n"
		"./server.py\n"
		"./server.py -help\n"
		"python3 server.py -motd 'This is my motd' -hostname 'the-inn' -port 1337\n"
		"./server.py -servername \"Yulgar's Inn\" -motdfile 'mymotd.txt')"
	)

	arg_types = {
		"-motd": str,
		"-motdfile": str,
		"-hostname": str,
		"-servername": str,
		"-ip": str,
		"-port": int
	}

	if len(args) > 1:
		parsed_args = {}
		for i in range(1, len(args), 2):
			if args[i] == "-help":
				print(help_msg)
				return 1
			elif i + 1 < len(args) and args[i] in arg_types.keys():
				if args[i + 1].isnumeric() and arg_types[args[i]] == int:
					args[i + 1] = int(args[i + 1])
				if isinstance(args[i + 1], arg_types[args[i]]):
					parsed_args[args[i][1:]] = args[i + 1]
			else:
				print(help_msg)
				return 1

		return parsed_args

	return 0


if __name__ == "__main__":
	pass