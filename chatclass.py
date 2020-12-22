import os
import random
import time
import csv
import random
import socket
import sys

#main class
class CHATBOT:
    def __init__(self, inputDict):
        #set to defaults or grab cli input from dict
        self.server = inputDict["-server"] if "-server" in inputDict else "::1"
        self.port = inputDict["-port"] if "-port" in inputDict else 6667
        self.channel = inputDict["-channel"] if "-channel" in inputDict else "#1"
        self.botnicks = inputDict["-nicks"] if "-nicks" in inputDict else [
            "scuffbot", "scuffy", "scuffo"]
        self.botnickindex =0
        self.botnick = self.botnicks[self.botnickindex] # select the first botnick 

        print("---BOT CONFIG---")
        print("Server          : ", self.server)
        print("Port            : ", self.port)
        print("Channel         : ",self.channel)
        print("Bot nick list   : ",self.botnicks)
        print("Current botnick : ",self.botnick)
        self.irc = self.IRC(self.server, self.port, self.channel, self.botnick)
        #read in files and facts 
        global fish
        fish = self.parseCSV("fish.csv")
        global facts
        facts = self.parseCSV("facts.csv")

    #split response into single messages
    def parseMessages(self, input):
        if input:
            input = input.split("\n")[:-1]
            return input
        else:
            return None
    #execute commands based on response
    def commands(self, text):
        global users # list of users in channel

        split = text.split()

        #handle nick and channel errors
        if split[1] == "403":
            print("channel: ",self.channel, " does not exist on the server")
            exit()

        if split[1] == "404":
            print(self.botnick , " is not allowed to send to ", self.channel)
            exit()

        if split[1] == "405":
            print(self.botnick, " has joined to many channels on the server")
            exit()

        if split[1] == "433" or split[1] == "432":  # error with nick
            print(
                self.botnick, " is already in use on server " if split[1] == "433" else " has erroneous chars")
            #if there is another nick to use then reconnect with it
            self.botnickindex +=1
            self.botnick = self.botnicks[self.botnickindex] if self.botnickindex < len(self.botnicks) else None
            if self.botnick is None:
                print("Exhausted nick list, exiting")
                exit()
            print("New nick : ", self.botnick)
            self.irc.botnick = self.botnick
            self.irc.connected = False

        #generate the initial userlist , not including the bot
        if split[1] == "353":
            users = text[text.rfind(":")+1:].split()
            users.remove(self.botnick)

        #find message sender
        messageNick = split[0][1:split[0].find("!")]

        #update user list with PART QUIT AND JOIN commands
        if len(split) >=3 and (split[1] == "PART" or split[1] == "QUIT"):
            if messageNick != self.botnick:
                users.remove(messageNick)
        if len(split) >= 3 and split[1] == "JOIN":
            if messageNick != self.botnick:
                users.append(messageNick)

        # private message commands
        if len(split) == 4 and "PRIVMSG" == split[1] and self.botnick == split[2]:
            messageText = split[3][1:]
            if messageText == "!fact":
                receiver = text[1:text.find("!")]
                fact = random.choice(facts)
                self.irc.sendpm(
                    receiver, "* Enjoy your fact: {} *".format(fact))

        # single argument bot commands 
        if len(split) == 4 and "PRIVMSG" == split[1] and self.channel == split[2] and split[3][0] == ':':
            
            #finds purely the command
            messageText = split[3][1:]

            if messageText == "!hello":
                sender = text[1:text.find("!")] # Finds out the sender
                self.irc.sendchan("Hah you're gay!" + sender + "!")

            # Replies with a random fish from a list of ~1000   
            elif messageText == "!fish":
                self.irc.sendchan("back in my day " +
                                  random.choice(fish) + " was the prize catch")

             # *Slaps* a random user from list of users in channel
            elif messageText == "!slap":
                slapper = messageNick  # find out the slapper
                slappee = slapper

                # Chooses a random user from current channel, or the slapper if they are the only user
                while slappee == slapper:
                    slappee = random.choice(users) if len(
                        users) > 1 else "...themselves (maybe invite a friend to slap next time)"
                self.irc.sendchan("* {} slaps {} *".format(slapper, slappee))

            # *Slaps* a random user with a fish from a list of ~1000 fish
            elif messageText == "!fishSlap":
                slapper = text[1:text.find("!")]  # finds out the slapper
                slappee = slapper

                # *Slaps* a random user with a fish from a list of ~1000 fish
                while slappee == slapper:
                    slappee = random.choice(users) if len(
                        users) > 1 else "...themselves"
                
                # Chooses a random fish
                weapon = random.choice(fish)
                self.irc.sendchan(
                    "* {} slaps {} with a {} *".format(slapper, slappee, weapon))
                    
            # As before *Slaps* a random user with a sock
            elif messageText == "!sock":
                slapper = text[1:text.find("!")]  # finds out the slapper
                slappee = slapper

                # Chooses a random user from current channel, or the slapper if they are the only user
                while slappee == slapper:
                    slappee = random.choice(users) if len(
                        users) > 1 else "...themselves"
                self.irc.sendchan(
                    channel, "* {} slaps {} with a sock *".format(slapper, slappee))
        # multiple argument bot commands
        if len(split) == 5 and "PRIVMSG" == split[1] and self.channel == split[2] and split[3][0] == ':':
            
            messageText = split[3][1:]

            #join the channel requested in chat
            if "!joinchan" == messageText:
                newChan = split[4]
                print("switching to : ",newChan, " as requested by : " , messageNick)
                self.irc.sendchan("switching to : " + newChan + " as requested by : " + messageNick)
                self.channel = newChan
                self.irc.channel = self.channel
                self.irc.connected = False
    #connect bot to irc server
    def connectIRC(self):
        while not self.irc.connected:
            print("attempting to connect")
            try:
                self.irc.connect()
                self.irc.connected = True
            except ConnectionRefusedError as identifier:
                self.irc.connected = False
                time.sleep(1)
                pass

    # Checks for incoming messages from server
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
                    print(command+"\n")
                    self.commands(command)

    #read csv from path
    def parseCSV(self, path):
        with open(path, 'r') as file:
            reader = csv.reader(file)
            return list(reader)[0]


    #class to handle irc socket communication
    class IRC:
        def __init__(self, server, port, channel, botnick):
            self.server = server
            self.port = port
            self.channel = channel
            self.botnick = botnick
            self.connected = False


        #create ipv6 socket with stream
        def initSocket(self):
            self.irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)


        #send message to the current channel
        def sendchan(self, msg):
            # Transfer data
            self.irc.send(bytes("PRIVMSG " + self.channel +
                                " :" + msg + "\n", "UTF-8"))


        #send message to the supplied user
        def sendpm(self, user, msg):
            self.irc.send(bytes("PRIVMSG " + user +
                                " :" + msg + "\n", "UTF-8"))

                                
        #send a who command //UNUSED
        def who(self, channel):
            self.irc.send(bytes("WHO " + self.channel + "\n", "UTF-8"))


        #send a nick command for currrent nick
        def nick(self):
            self.irc.send(bytes("NICK " + self.botnick + "\n", "UTF-8"))


        #send a join command for current channel
        def join(self):
            self.irc.send(bytes("JOIN " + self.channel + "\n", "UTF-8"))


        #
        def connect(self, service=False):
            self.initSocket()
            print("Connecting to: " + self.server + " " + str(self.port) + " " +self.channel + " as: "+self.botnick)
            try:
                self.irc.connect((self.server, self.port))
            except socket.gaierror as e:
                print("server : ", self.server, " | port ", self.port)
                print(e)
                exit()
            except OSError as e:
                print("server : ", self.server, " | port ", self.port)
                print(e)
                exit()
                #//UNUSED
            if service:
                self.irc.send(bytes("SERVICE " + self.botnick +
                                    " " + ":chatbot "+"\n", "UTF-8"))
            else:
                self.irc.send(bytes("USER " + self.botnick + " 0  * " + " :REALNAME\n", "UTF-8"))
            self.nick()
            time.sleep(1)
            self.join()

        #decode response as string and reply to any PING commands
        def getResponseString(self):
            resp = self.irc.recv(2040).decode("UTF-8")
            if resp[:4] == "PING":
                self.irc.send(
                    bytes('PONG ' + resp.split()[1] + '\r\n', "UTF-8"))
            return resp
        pass


#get commmand line args
sys.argv.pop(0)
args = sys.argv
#if help only help
if len(args) == 1 and args[0] == "-help":
    print("help command")
    exit()

#flag commmands
def server(inputList):
    if len(inputList) != 1:
        print("-server : expecting 1 input was given : ", inputList)
        return None
    return inputList[0]


def port(inputList):
    if len(inputList) != 1:
        print("-port : expecting 1 input was given : ", inputList)
        return None
    try:
        conv = int(inputList[0])
        return conv
    except ValueError:
        print("invalid input for port  : ", inputList[0])
        return None


def channel(inputList):
    if len(inputList) != 1:
        print("-channel : expecting 1 input was given : ", inputList)
        return None
    return inputList[0]


def nick(inputList):
    return inputList

def nickfile(inputList):
    if len(inputList) != 1:
        print("-nickfile expecting 1 input was given : ", inputList)
        return None
    if os.path.exists(inputList[0]):
       with open(inputList[0],'r') as f:
           try:
               lines = f.read().splitlines()
               return lines
           except : 
               print("error with file")
               return None
    else:
        print("file : ",inputList[0], " does not exist")
        return None
    return None


#ARGUMENT PARSING
#----------------
#possible args
possArgs = {"-server": server, "-port": port,
            "-channel": channel, "-nick": nick, "-nickfile": nickfile}
index = 0
argsParsed = {}
cur = list()
curkey = ""
while index < len(args):
    if args[index].lower() in possArgs:
        if curkey:
            if curkey in argsParsed:
                print("error two of ", curkey, " provided")
                exit()
            argsParsed[curkey] = cur
        cur = list()
        curkey = args[index]
    else:
        if args[index]:
            cur.append(args[index])

    index += 1
if curkey:
    if curkey in argsParsed:
        print("error two of ", curkey, " provided")
        exit()
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
chat = CHATBOT(finalArgs)
chat.run()
