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
users = list()
irc.connect(server, port, channel, botnick, botpass, botnickpass)
with open('fish.csv', 'r') as file:
    reader = csv.reader(file)
    fish = list(reader)[0]


def commands(text):
    global users
    if len(text.split()) > 3 and "=" == text.split()[3]:
        users = text[text.rfind(":")+1:].split()
        users.remove(botnick)
    if len(text.split()) == 4 and text.split()[1] == "PART" and text.split()[3] == "::Leaving":
        if text[1:text.find("!")] != botnick:
            users.remove(text[1:text.find("!")])
    if len(text.split()) == 3 and text.split()[1] == "JOIN":
        if text[1:text.find("!")] != botnick:
            users.append(text[1:text.find("!")])
    if "PRIVMSG" == text.split()[1] and botnick == text.split()[2]:  # private message
        irc.send(text[1:text.find("!")], random.choice(fish))
    if len(text.split()) == 4 and "PRIVMSG" == text.split()[1] and channel == text.split()[2] and text.split()[3][0] == ':': # normal message
        messageText = text.split()[3][1:]
        if messageText == "!hello":
            irc.send(channel, "Hah you're gay!" + botnick)
        elif messageText == "!fish":
            irc.send(channel, "back in my day " +
                 random.choice(fish) + " was the prize catch")
        elif messageText == "!slap":
            print(text.split())
            slapper = text[1:text.find("!")]  # find out the slapper
            slappee = random.choice(users) if len(
            users) > 0 else "...themselves (maybe invite a friend to slap next time)"
            irc.send(channel, "* {} slaps {} *".format(slapper, slappee))

def parseMessages(input):
    if input:
        print(input)
        input = input.split("\n")[:-1]
        return input
    else:
        return None


while True:
    text = irc.get_response()

    parsed = parseMessages(text)
    if parsed is None:
        time.sleep(2)
        print("reconnecting")
        irc = None
        while irc is None:
            try:
                irc = IRC()
                irc.connect(server, port, channel,
                            botnick, botpass, botnickpass)
            except ConnectionRefusedError as identifier:
                irc = None
                time.sleep(1)
                pass
    else:
        for command in parsed:
            commands(command)
