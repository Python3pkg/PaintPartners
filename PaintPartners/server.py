import socket,select,queue,json,random,sys,configparser,getpass,imp,re
from threading import Thread
from time import sleep
from urllib.request import urlopen
     
def parse_message(data,typeMessage=""):
    return [_f for _f in re.split('[_\|]', data) if _f]

def parse_data(data):
    return [_f for _f in re.split('[{}]', data) if _f] 

def removekey(dictionary, key):
    r = dict(dictionary)
    del r[key]
    return r

class ServerListenThread(Thread):
    def __init__(self,server):
        super(ServerListenThread, self).__init__()
        self.running = True
        self.server = server

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 6121
        self.s.bind((self.host, self.port))
        print((str(self.host) + " Listening on port : " + str(self.port)+"\r\n"))
        self.s.listen(10)
        
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            try:
                connection, address = self.s.accept()
                thread = ClientThread(self.server,connection,address[0])
                thread.start()
                self.server.clients[address[0]] = thread
            except socket.error as msg:
                print(("Socket error!: " + str(msg)))
                pass
                    
class ProcessThread(Thread):
    def __init__(self,server):
        super(ProcessThread, self).__init__()
        self.running = True
        self.q = queue.Queue()
        self.server = server
        self.username = ""
    def add(self, data, username):
        self.q.put(data)
        self.username = username
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            if not self.q.empty():
                value = self.q.get(block=True)
                self.server.process(value,self.username)
                self.username = ""
                
            #clean up any innactive threads
            for key,value in list(self.server.clients.items()):
                if value.running == False:
                    print(("Removing Client: " + key))
                    self.server.broadcast_notsource("_DISCONNECT_|" + key,key)
                    self.server.clients = removekey(self.server.clients,key)

class ClientThread(Thread):
    def __init__(self,server,socket,address):
        super(ClientThread, self).__init__()
        self.running = True
        self.conn = socket
        self.username = address
        self.address = address
        self.server = server
    def stop(self):
        self.running = False
    def run(self):
        while self.running:
            try:
                data = self.conn.recv(9999999)
                if data:
                    if not "_CONNECT_" in data:
                        self.server.process_thread.add(data,self.username)
                    else:
                        self.server.process_init(data,self)
            except socket.error as msg:
                print(("Socket error!: " + str(msg)))
                self.running = False
                pass
        print("Closing connection...")
        self.conn.close()

class InputThread(Thread):
    def __init__(self,server):
        super(InputThread, self).__init__()
        self.running = True
        self.server = server
    def run(self):
        while self.running:
            userinput = input()
            if userinput == "print clients":
                self.server.print_clients()
            elif userinput == "print clients detail":
                self.server.print_clients_detail()
            elif userinput[:4] == "kick":
                if userinput != "kick":
                    if self.server.program.admin == userinput[5:]:
                        print("Cannot kick the admin from the server!")
                    else:
                        self.server.reply_to_client_username("_KICK_",userinput[5:])
            elif userinput[:4] == "lock":
                if userinput == "lock":
                    self.server.broadcast_noadmin("_LOCK_")
                else:
                    self.server.reply_to_client_username("_LOCK_",userinput[5:])
            elif userinput[:6] == "unlock":
                if userinput == "unlock":
                    self.server.broadcast_noadmin("_UNLOCK_")
                else:
                    self.server.reply_to_client_username("_UNLOCK_",userinput[7:])
            elif userinput[:4] == "help":
                print("\r\n----------------------------------------------------------------------------")
                print("----------------------------SERVER COMMANDS---------------------------------")
                print("\r\nprint clients: prints the list of all connected clients")
                print("\r\nprint clients detail: prints the list of all connected clients,\ntheir IP Addresses, and wether or not their sockets are connected")
                print("\r\nkick <username>: kicks the specified client from the\nserver (example: kick rob)")
                print("\r\nlock: prevents all currently connected clients from modifying\nthe paint board")
                print("\r\nlock <username>: prevents the specified client from modifying\nthe paint board (example: lock rob)")
                print("\r\nunlock: gives all currently connected clients permission to\nmodify the paint board")
                print("\r\nunlock <username>: gives the specified client permission to\nmodify the paint board (example: unlock rob)")
                print("\r\nhelp: prints out the commands useable by the server admin and\nwhat each command does")
                print("----------------------------------------------------------------------------\r\n")

class Server():
    def __init__(self):
        self.clients = {}
        self.admin = ""
        self.load_cfg()
    
        self.process_thread = ProcessThread(self)
        self.input_thread = InputThread(self)
        self.process_thread.start()
        self.input_thread.start()
        
        self.server_listen_thread = ServerListenThread(self)
        self.server_listen_thread.start()

        try:
            m = imp.load_source('main', 'main.pyw')
            self.program = m.Program(True)
        except:
            m = imp.load_source('main', 'main.py')
            self.program = m.Program(True)
            
    def print_clients(self):
        message = "\nConnected Clients: ["
        for key,value in self.clients.items():
            message += str(key)+","
        message = message[:-1]
        message += "]\n"
        print(message)
        
    def print_clients_detail(self):
        print("\r\n----------------------------------")
        print("----------------------------------")
        print("Connected Clients")
        print("----------------------------------")
        for key,value in self.clients.items():
            print("----------------------------------")
            print(("Username:   " + str(value.username)))
            print(("Connected:  " + str(value.running)))
            print(("Address:    " + str(value.address)))
            print("----------------------------------")
        print("----------------------------------\r\n")
        
        
    def load_cfg_yesorno(self,config,key,printstatement):
        while True:
            inputstr = input(printstatement)
            if inputstr.lower() == "y":
                config.set('ServerInfo',key,"1")
                break
            elif inputstr.lower() == "n":
                config.set('ServerInfo',key,"0")
                break
            else:
                print(("'"+inputstr+"' is not a valid answer."))
                
    def load_cfg(self):
        config = configparser.RawConfigParser()
        try:
            config.readfp(open('server.cfg'))
        except Exception as e:
            config.add_section('ServerInfo')
            print('We need a moment to set up your server, please fill in the prompts below...')

            serverpassword = getpass.getpass("Please specify your server password: ")
            config.set('ServerInfo','serverpass',serverpassword)
            
            username = input("Please specify your admin username: ")
            config.set('ServerInfo','adminname',username)
            
            self.load_cfg_yesorno(config,"AllowEdits","Allow clients to edit drawing board? (type 'y' for 'yes', 'n' for 'no'): ")
            #self.load_cfg_yesorno(config,"ClientDatabase","Restrict clients to specific names and passwords? (type 'y' for 'yes', 'n' for 'no'): ")

            with open('server.cfg', 'w') as configfile:
                config.write(configfile)
          
    def broadcast(self,message):
        for key,value in self.clients.items():
            value.conn.send("{"+message+"}")
    def broadcast_noadmin(self,message):
        for key,value in self.clients.items():
            if key != self.admin:
                value.conn.send("{"+message+"}")
    def broadcast_notsource(self,message,username):
        for key,value in self.clients.items():
            if key != username:
                value.conn.send("{"+message+"}")
                
    def reply_to_client(self,message,source_socket):
        source_socket.send("{"+message+"}")
        
    def reply_to_client_username(self,message,username):
        if not username in list(self.clients.keys()):
            print(("Could not find username: " + username))
            return
        self.clients[username].conn.send("{"+message+"}")

    def process_init(self,data,client_thread):
        if data:
            print(data)
            blocks = parse_data(data)
            for block in blocks:
                if "_CONNECT_" in block:
                    messages = parse_message(block,"_CONNECT_")
                    for key,value in self.clients.items():
                        if key == messages[1]:
                            self.reply_to_client("_INVALIDUSERNAME_",client_thread.conn)
                            return
                    config = configparser.RawConfigParser()
                    config.readfp(open('server.cfg'))
                    serverPass = config.get('ServerInfo', 'serverpass')

                    if messages[2] != serverPass:
                        self.reply_to_client("_INVALIDPASSWORD_",client_thread.conn)
                        return

                    address_copy = client_thread.address
                    client_thread.username = messages[1]
                    self.clients[messages[1]] = client_thread
                    self.clients = removekey(self.clients,address_copy)
                    self.print_clients()
     
                    canEdit = config.get('ServerInfo', 'allowedits')
                    if canEdit == "1":
                        self.reply_to_client("_CONNECTVALID_",client_thread.conn)
                    else:
                        self.reply_to_client("_CONNECTVALIDNOEDIT_",client_thread.conn)

                    msg = ""
                    for key,value in list(self.clients.items()):
                        msg += key + "|"
                    msg = msg[:-1]
                    self.broadcast("_CONNECT_" + msg)

    #This method prcesses string data          
    def process(self,data,username):
        if data:
            blocks = parse_data(data)
            
            client_thread = None
            #get client thread to work with
            for key,value in self.clients.items():
                if key == username:
                    client_thread = value
                    break
            for block in blocks:
                if "_CHATMESSAGE_" in block:
                    self.broadcast(block)
                elif "_PIXELDATA_" in block:
                    self.broadcast_notsource(block,username)
                elif "_BRUSHDATA_" in block:
                    self.broadcast_notsource(block,username)
                elif "_MOUSEDATA_" in block:
                    self.broadcast_notsource(block,username)
                elif "_REQUESTIMAGE_" in block:
                    imgdata = self.program.image.tostring()
                    self.reply_to_client_username("_FULLDATA_" + imgdata,username)
                elif "_DISCONNECT_" in block:
                    li = parse_message(block,"_DISCONNECT_")
                    self.broadcast(block)
                    print(("Removing Client: " + li[1]))
                    self.clients = removekey(self.clients,li[1])
                    
        
    def main(self):
        while True:
            self.program.main()
            
        self.process_thread.stop()
        self.process_thread.join()
        self.input_thread.stop()
        self.input_thread.join()
        self.server_listen_thread.stop()
        self.server_listen_thread.join()

if __name__ == "__main__":
    server = Server()
    server.main()
