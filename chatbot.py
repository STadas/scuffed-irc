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
irc = None
fish = list()
users = list()
with open('fish.csv', 'r') as file:
    reader = csv.reader(file)
    fish = list(reader)[0]

def commands(text):
    global users
    split = text.split()
    if len(split) > 3 and "=" == split[3]:
        users = text[text.rfind(":")+1:].split()
        users.remove(botnick)
    messageNick = split[0][1:split[0].find("!")]
    if len(split) == 4 and split[1] == "PART" and split[3] == "::Leaving":
        if messageNick != botnick:
            users.remove(messageNick)
    if len(split) == 3 and split[1] == "JOIN":
        if messageNick != botnick:
            users.append(messageNick)
    if len(split) == 4 and "PRIVMSG" == split[1] and botnick == split[2]:  # private message
        irc.send(messageNick, random.choice(fish))
    if len(split) == 4 and "PRIVMSG" == split[1] and channel == split[2] and split[3][0] == ':': # normal message
        messageText = split[3][1:]
        if messageText == "!hello":
            irc.send(channel, "Hah you're gay!" + botnick)
        elif messageText == "!fish":
            irc.send(channel, "back in my day " +
                 random.choice(fish) + " was the prize catch")
        elif messageText == "!slap":
            slapper = messageNick  # find out the slapper
            slappee = slapper
            while slappee==slapper:
                slappee = random.choice(users) if len( users) > 1 else "...themselves (maybe invite a friend to slap next time)"
            irc.send(channel, "* {} slaps {} *".format(slapper, slappee))
        elif messageText == "!fishSlap":
            print(text.split())
            slapper = text[1:text.find("!")] # finds out the slapper
            slappee = slapper
            while slappee == slapper:
                slappee = random.choice(users) if len(users) > 1 else "...themselves"
            weapon = random.choice(fish)
            irc.send(channel, "* {} slaps {} with a {} *".format(slapper,slappee,weapon))
def parseMessages(input):
    if input:
        print(input)
        input = input.split("\n")[:-1]
        return input
    else:
        return None
def connectIRC():
    global irc
    while irc is None:
            try:
                irc = IRC()
                irc.connect(server, port, channel,
                            botnick, botpass, botnickpass)
            except ConnectionRefusedError as identifier:
                irc = None
                time.sleep(1)
                pass

while True:
    connectIRC()
    text = irc.get_response()
    parsed = parseMessages(text)
    if parsed is None:
        time.sleep(2)
        print("reconnecting")
        irc = None
        users.clear()
        connectIRC()
    else:
        for command in parsed:
            commands(command)
