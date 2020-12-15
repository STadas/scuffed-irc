from irc_class import *
import os
import random

## IRC Config
server = socket.gethostname() # Provide a valid server IP/Hostname
port = 6667
channel = "#1"
botnick = "scuffbot"
botnickpass = "guido"
botpass = "<%= @guido_password %>"
irc = IRC()
irc.connect(server, port, channel, botnick, botpass, botnickpass)

while True:
    text = irc.get_response()
    print(text)
 
    if "!hello" in text and channel in text:
        irc.send(channel, "Hah you're gay!" + botnick)
    if "!gay" in text and channel:
        irc.send(channel, "No u")