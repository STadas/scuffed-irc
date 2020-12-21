from chatclass import *
import os
import random
import time
import csv
import random
# IRC Config

server = "::1"  # Provide a valid server IP/Hostname
port = 6667

channel = "#1" # Default channel to join
botnick = "scuffbot" # Nickname

irc = None

# Lists for random selection
fish = list()
users = list()
facts = list()

# File reading into list for fish and facts

with open('fish.csv', 'r') as file:
    reader = csv.reader(file)
    fish = list(reader)[0]

with open('facts.csv','r') as file:
    reader = csv.reader(file)
    facts = list(reader)[0]


# List of possible commands
def commands(text):
    global users # list of users in channel
    split = text.split()

    # Generates list of users in channel not including the bot itself
    if len(split) > 3 and "=" == split[3]:
        users = text[text.rfind(":")+1:].split()
        users.remove(botnick)

    # Finds message sender     
    messageNick = split[0][1:split[0].find("!")]
    if len(split) == 4 and split[1] == "PART" and split[3] == "::Leaving":
        if messageNick != botnick:
            users.remove(messageNick)
    if len(split) == 3 and split[1] == "JOIN":
        if messageNick != botnick:
            users.append(messageNick)

    # Private message commands
    if len(split) == 4 and "PRIVMSG" == split[1] and botnick == split[2]:
        messageText = split[3][1:]
        if messageText == "!fact":
            print(text.split())
            receiver = text[1:text.find("!")]
            fact = random.choice(facts)
            irc.send(receiver, "* Enjoy your fact: {} *".format(fact))

    # Single argument bot commands
    if len(split) == 4 and "PRIVMSG" == split[1] and channel == split[2] and split[3][0] == ':':

        # Finds purely the command
        messageText = split[3][1:]
        if messageText == "!hello":
            sender = text[1:text.find("!")] # Finds out the sender
            irc.send(channel, "Hello " + sender + "!") # Sends message to chat

        # Replies with a random fish from a list of ~1000
        elif messageText == "!fish":
            irc.send(channel, "back in my day " + random.choice(fish) + " was the prize catch")

        # *Slaps* a random user from list of users in channel
        elif messageText == "!slap":
            slapper = messageNick  # Find out the slapper
            slappee = slapper

            # Chooses a random user from current channel, or the slapper if they are the only user
            while slappee==slapper:
                slappee = random.choice(users) if len( users) > 1 else "...themselves (maybe invite a friend to slap next time)"
            irc.send(channel, "* {} slaps {} *".format(slapper, slappee))

        # *Slaps* a random user with a fish from a list of ~1000 fish
        elif messageText == "!fishSlap":
            print(text.split())
            slapper = text[1:text.find("!")] # Finds out the slapper
            slappee = slapper

            # Chooses a random user from current channel, or the slapper if they are the only user
            while slappee == slapper:
                slappee = random.choice(users) if len(users) > 1 else "...themselves"

            # Chooses a random fish
            weapon = random.choice(fish)
            irc.send(channel, "* {} slaps {} with a {} *".format(slapper,slappee,weapon))


        # As before *Slaps* a random user with a sock
        elif messageText == "!sock":
            print(text.split())
            slapper = text[1:text.find("!")] # Finds out the slapper
            slappee = slapper

            # Chooses a random user from current channel, or the slapper if they are the only user
            while slappee == slapper:
                slappee = random.choice(users) if len(users) > 1 else "...themselves"
            irc.send(channel, "* {} slaps {} with a sock *".format(slapper,slappee))

    # Multiple argument commands
    if len(split) == 5 and "PRIVMSG" == split[1] and channel == split[2] and split[3][0] == ':':
            messageText = split[3][1:]
            if "!joinchan" in messageText:
                newChan = split[4]
                channel = newChan
                irc.join()


def parseMessages(input):
    if input:
        print(input)
        input = input.split("\n")[:-1]
        return input
    else:
        return None

# Connects bot to IRC server
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

# Checks for incoming messages from server
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
