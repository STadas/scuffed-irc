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


if __name__ == "__main__":
	pass