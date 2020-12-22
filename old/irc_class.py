import socket
import sys
import time

class IRC:

    irc = socket.socket()

    def __init__(self):
        # Define the socket
        self.irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    def send(self, channel, msg):
        # Transfer data
        self.irc.send(bytes("PRIVMSG " + channel + " :" + msg + "\n", "UTF-8"))
    
    def who(self,channel):
        print("WHO " + channel + " : "+ "\n", "UTF-8")
        self.irc.send(bytes("WHO " + channel + "\n", "UTF-8"))
    
    def connect(self, server, port, channel, botnick, botpass, botnickpass):
        # Connect to the server
        print("Connecting to: " + server)
        self.irc.connect((server, port))

        # Perform bot authentication
        self.irc.send(bytes("SERVICE " + botnick + " :A fun bot for your irc server", "UTF-8"))
        time.sleep(1)

        # join the default channel
        self.irc.send(bytes("JOIN " + channel, "UTF-8"))

    def get_response(self):
        resp = self.irc.recv(2040).decode("UTF-8")

        if resp[:4] == "PING":
            self.irc.send(bytes('PONG ' + resp.split()[1] + '\r\n', "UTF-8")) 

        return resp
    
    def joinchan(channel):

        self.irc.joinChannel(self, channel)