import socket
import pickle

HEADERSIZE = 10

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 6667))
s.listen(5)

print("Server started.")

while True:
	clientsocket, address = s.accept()
	print(f"Connection from {address} established.")

	d = {1: "Hey", 2: "There"}
	msg = pickle.dumps(d)
	msg = bytes(f"{len(msg):<{HEADERSIZE}}", "utf-8") + msg

	clientsocket.send(msg)
