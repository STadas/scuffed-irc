from irc_class import *
import os
import random
import time
import csv
import random
# IRC Config
server = "::1"  # Provide a valid server IP/Hostname
port = 6667
channel = "#1"
botnick = "scuffbot"
botnickpass = "guido"
botpass = "<%= @guido_password %>"
irc = IRC()
fish = list()
irc.connect(server, port, channel, botnick, botpass, botnickpass)
with open('fish.csv', 'r') as file:
    reader = csv.reader(file)
    fish = list(reader)[0]

while True:
    text = irc.get_response()
    print("~" + text + "~")
    if text:
        if "PRIVMSG" == text.split()[1] and botnick == text.split()[2]:
            irc.send(text[1:text.find("!")],random.choice(fish))
        if "!hello" in text and channel in text:
            irc.send(channel, "Hah you're gay!" + botnick)
        if "!fish" in text and channel:
            irc.send(channel, random.choice(fish))
        if "!slap" in text and channel:
            irc.who(channel) # request information on potential slapper and slappee's
            slapper = text[1:text.find("!")]  # find out the slapper
            cur = irc.get_response()  # get the information on potential slapper and slappee's
            userlist = list(map(lambda x: x.split()[7], list(filter(lambda x: len(x.split(
            )) == 11 and x.split()[7] != botnick and x.split()[7] != slapper, cur.split("\n")))))
            irc.send(channel, "* {} slaps {} *".format(slapper, random.choice(userlist)))
    else:
        time.sleep(2)
        print("reconnecting")
        irc = None
        while irc is None:
            try:
                irc = IRC()
                irc.connect(server, port, channel, botnick, botpass, botnickpass)
            except ConnectionRefusedError as identifier:
                irc = None
                time.sleep(1)
                pass
        
       