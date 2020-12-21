import os
import random
import time
import csv
import random
import socket
import sys


class CHATBOT:
    class IRC:
        irc = socket.socket()

        def __init__(self, server, port, channel, botnick, ipv6=True):
            self.server = server
            self.port = port
            self.channel = channel
            self.ipv6 = ipv6  # TODO: remove IPV6
            self.botnick = botnick
            self.connected = False

        def initSocket(self):
            if self.ipv6:
                self.irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        def sendchan(self, msg):
            # Transfer data
            self.irc.send(bytes("PRIVMSG " + self.channel +
                                " :" + msg + "\n", "UTF-8"))

        def sendpm(self, user, msg):
            self.irc.send(bytes("PRIVMSG " + user +
                                " :" + msg + "\n", "UTF-8"))

        def who(self, channel):
            self.irc.send(bytes("WHO " + channel + "\n", "UTF-8"))

        def connect(self, service=False):
            self.initSocket()
            print("Connecting to: " + self.server)
            self.irc.connect((self.server, self.port))
            if service:
                self.irc.send(bytes("SERVICE " + self.botnick +
                                    " " + ":chatbot "+"\n", "UTF-8"))
            else:
                self.irc.send(bytes("USER " + self.botnick + " " +
                                    self.botnick + " " + self.botnick + " :python\n", "UTF-8"))
            self.irc.send(bytes("NICK " + self.botnick + "\n", "UTF-8"))
            time.sleep(1)
            # join the channel
            self.irc.send(bytes("JOIN " + self.channel + "\n", "UTF-8"))

        def getResponseString(self):
            resp = self.irc.recv(2040).decode("UTF-8")
            if resp[:4] == "PING":
                self.irc.send(
                    bytes('PONG ' + resp.split()[1] + '\r\n', "UTF-8"))
            return resp
        pass

    def __init__(self,inputDict):
        self.server = inputDict["-server"] if "-server" in inputDict else "::1"
        self.port = inputDict["-port"] if "-port" in inputDict else 6667
        self.channel = inputDict["-channel"] if "-channel" in inputDict else "#1"
        self.botnicks = inputDict["-nicks"] if "-nicks" in inputDict else ["scuffbot","scuffy","scuffo"]
        self.botnick = self.botnicks[0] #TODO: fix
        print(self.botnick)
        self.irc = self.IRC(self.server, self.port, self.channel,self.botnick)
        global fish
        fish = self.parseCSV("fish.csv")
        global facts
        facts = self.parseCSV("facts.csv")

    def parseMessages(self, input):
        if input:
            print(input)
            input = input.split("\n")[:-1]
            return input
        else:
            print("empty input")#TODO:remove
            return None

    def commands(self, text):
        global users
        split = text.split()
        if split[1] == "433" or split[1] =="432":  #error nick
            print(self.botnick, " is already in use on server " if split[1]=="433" else " has erroneous chars")
            self.botnick = self.botnicks[self.botnicks.index(self.botnick)+1] if self.botnicks.index(self.botnick)+1 < len(self.botnicks) else None
            if self.botnick is None:
                print("Exhausted nick list, exiting")
                exit()
            print("New nick : ",self.botnick)
            self.irc.botnick = self.botnick
            self.irc.connected = False
        if len(split) > 3 and "=" == split[3]:
            users = text[text.rfind(":")+1:].split()
            users.remove(self.botnick)
        messageNick = split[0][1:split[0].find("!")]
        if len(split) == 4 and (split[1] == "PART" or split[1] == "QUIT")  and split[3] == "::Leaving":
            if messageNick != self.botnick:
                users.remove(messageNick)
        if len(split) == 3 and split[1] == "JOIN":
            if messageNick != self.botnick:
                users.append(messageNick)
        # private message
        if len(split) == 4 and "PRIVMSG" == split[1] and self.botnick == split[2]:
            messageText = split[3][1:]
            if messageText == "!fact":
                receiver = text[1:text.find("!")]
                fact = random.choice(facts)
                self.irc.sendpm(
                    receiver, "* Enjoy your fact: {} *".format(fact))
        # normal message
        if len(split) == 4 and "PRIVMSG" == split[1] and self.channel == split[2] and split[3][0] == ':':
            messageText = split[3][1:]
            if messageText == "!hello":
                self.irc.sendchan("Hah you're gay!" + self.botnick)
            elif messageText == "!fish":
                self.irc.sendchan("back in my day " +
                                  random.choice(fish) + " was the prize catch")
            elif messageText == "!slap":
                slapper = messageNick  # find out the slapper
                slappee = slapper
                while slappee == slapper:
                    slappee = random.choice(users) if len(
                        users) > 1 else "...themselves (maybe invite a friend to slap next time)"
                self.irc.sendchan("* {} slaps {} *".format(slapper, slappee))
            elif messageText == "!fishSlap":
                slapper = text[1:text.find("!")]  # finds out the slapper
                slappee = slapper
                while slappee == slapper:
                    slappee = random.choice(users) if len(
                        users) > 1 else "...themselves"
                weapon = random.choice(fish)
                self.irc.sendchan(
                    "* {} slaps {} with a {} *".format(slapper, slappee, weapon))
            elif messageText == "!sock":
                slapper = text[1:text.find("!")]  # finds out the slapper
                slappee = slapper
                while slappee == slapper:
                    slappee = random.choice(users) if len(
                        users) > 1 else "...themselves"
                self.irc.sendchan(
                    channel, "* {} slaps {} with a sock *".format(slapper, slappee))

    def connectIRC(self):
        while not self.irc.connected:
            try:
                self.irc.connect()
                self.irc.connected = True
            except ConnectionRefusedError as identifier:
                self.irc.connected = False
                time.sleep(1)
                pass

    def run(self):
        while True:
            self.connectIRC()
            parsed = self.parseMessages(self.irc.getResponseString())
            if parsed is None:
                time.sleep(2)
                print("reconnecting")
                self.irc.connected = False
                users.clear()
                self.connectIRC()
            else:
                for command in parsed:
                    self.commands(command)

    def parseCSV(self, path):
        with open(path, 'r') as file:
            reader = csv.reader(file)
            return list(reader)[0]


sys.argv.pop(0)
args = sys.argv
# print(args)
def server(inputList):
    if len(inputList) != 1:
        print("expecting 1 input was given : ", inputList)
        return None
    return inputList[0]
def port(inputList):
    if len(inputList) != 1:
        print("expecting 1 input was given : ", inputList)
        return None
    return inputList[0]
def channel(inputList):
    if len(inputList) != 1:
        print("expecting 1 input was given : ", inputList)
        return None
    return inputList[0]
def nick(inputList):
    return inputList #TODO: nick checking
def nickfile(inputList):
    return inputList #TODO: nick checking
possArgs = {"-server":server, "-port":port, "-channel":channel, "-nick":nick, "-nickfile":nickfile}
index = 0
argsParsed = {}
cur = set()
curkey = ""
while index < len(args):
    if args[index].lower() in possArgs:
        if curkey:
            if curkey in argsParsed:
                # raise error
                print("error two of ",curkey," provided")
            argsParsed[curkey] = cur
        cur = set()
        curkey = args[index]
    else:
        if args[index]:
            cur.add(args[index])

    index += 1
if curkey:
    if curkey in argsParsed:
        # raise error
        print("error two of ",curkey," provided")
    argsParsed[curkey] = cur
finalArgs = {}
for arg in possArgs:
    if arg in argsParsed:
        argsCorrect = possArgs[arg](list(argsParsed[arg]))
        if argsCorrect is None:
            print("ERROR")
            exit()
        if arg == "-nick" or arg == "-nickfile":
            if '-nicks' in finalArgs:
                finalArgs['-nicks'] += argsCorrect
            else:
                finalArgs['-nicks'] = argsCorrect
        else:
            finalArgs[arg] = argsCorrect

# server
# port
# channel
# ipv6
# nicks
print(finalArgs)
chat = CHATBOT(finalArgs)
chat.run()
