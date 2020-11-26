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

users = {}
channels = {}
hostname = "the hut"
IP = "127.0.0.1"
PORT = 6667

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}

print("Server started.")

while True:
	read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
	for notified_socket in read_sockets:
		if notified_socket == server_socket:
			client_socket, client_address = server_socket.accept()
			msg = client_socket.recv(2 ** 20)
			print("--------- CONN_ESTAB_START ---------")
			print(msg.decode("utf-8")))
			if msg.startswith(b"CAP LS") and len(msg.decode("utf-8")) == 12:
				msg = client_socket.recv(2 ** 20)
				print(msg.decode("utf-8"))
			print("---------- CONN_ESTAB_END ----------")