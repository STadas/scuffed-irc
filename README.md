# **scuffed-irc**
A basic implementation of an IRC server and bot in python for the 2nd assignment of AC31008 - Networks and Data Communications

---
## **Server Instructions**

### **Examples**
`python3 server.py`<br>
`./server.py`<br>
`./server.py -help`<br>
`python3 server.py -motd 'This is my motd' -hostname 'the-inn' -port 1337`<br>
`./server.py -servername "Yulgar's Inn" -motdfile 'mymotd.txt'`<br>

### **Available flags**
Flag | Description
-|-
`-help` | displays this help message
`-motd` | sets motd to provided string
`-motdfile` | sets MOTD file to read from \(overrides `-motd` if specified file exists\)
`-hostname` | sets hostname to use
`-servername` | sets server name to use
`-ip` | sets IP to use
`-port` | sets port to listen to

### **Defaults**
Option | Default
-|-
`motd` | 'No MOTD set.'
`motdfile` | 'motd.txt'
`hostname` | your device's hostname
`servername` | \<`hostname`\>'s server
`ip` | ::, which is any IPv6 of your device in the local network \(e.g. ::1, localhost, etc.\)
`port` | 6667

---
## **Bot Instructions**
### **Chat Commands**: Send these commands to a channel that the bot is in
Command | Description
-|-
`!hello` | Replies to the sender with a message and the current time.
`!fish` | Sends a message to the chat with a name of a fish from a list of ~1000 fish.
`!slap` | Sends a message to the chat stating; "\<Sender\> slaps \<Random user\>" where 'Sender' is the user who typed the command and 'Random user' is a random user from list of current users in the channel.
`!fishSlap` | Sends a message to the chat stating; "\<Sender\> slaps \<Random user\> with a \<Fish\>" where 'Sender' is the user who typed the command and 'Random user' is a random user from a list of current users in the channel and 'Fish' is a random fish from a list of ~1000 fish.
`!sock` | Sends a message to the chat stating; "\<Sender\> slaps \<Random user\> with a sock" where 'Sender' is the user who typed the command and 'Random user' is a random user from a list of current users in the channel.

### **PM Commands**: Send these commands as a personal message to the bot 
Command | Description
-|-
`!fact` | Sends a random fact as a PM to the user

### **Examples**
`python3 chatbot.py`<br>
`python3 chatbot.py -help`<br>
`python3 chatbot.py -server ::1 -port 6667 -nick nick1 nick2 -nickfile nicks.txt`<br>
`python3 chatbot.py -channel #mycoolchan -nick cooldude`<br>

### **Available flags**
Flag | Description
-|-
`-help ` | display help message
`-server ` | the server to join
`-port ` | the port on the server
`-channel` | the channel to join
`-nick`* | space seperated list of nicks  
`-nickfile`* | path to file of line seperated list of nicks

*nick flags can both be used together and will allow duplicates in the list

### **Defaults**
Option | Value
-|-
`server` | ::1
`port` | 6667
`channel` | #1
`nicks` | scuffbot , scuffy , scuffo
