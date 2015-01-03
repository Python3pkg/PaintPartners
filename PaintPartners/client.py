import sys,socket,thread,select,pygame,json,Queue,ConfigParser
from urllib2 import urlopen
from time import sleep
from threading import Thread

def parse_message(message,typeMessage=""):
    messageList = []
    count = 0
    part = ''
    for char in message:
        if count != 0:
            if count > len(typeMessage)-1:
                if char == "_" or char == "|":
                    messageList.append(part)
                    part = ''
                else:
                    part += char
                    if count == len(message) - 1:
                        messageList.append(part)
                        part = ''
        count += 1
    return messageList

class ClientThreadSend(Thread):
    def __init__(self,client,socket):
        super(ClientThreadSend, self).__init__()
        self.daemon = True
        self.running = True
        self.conn = socket
        self.q = Queue.Queue()
        self.client = client
    def add(self,data):
        self.q.put(data)
    def stop(self):
        self.running = False
    def run(self):
        while self.running == True:
            try:
                if not self.q.empty():
                    message = self.q.get(block=True)
                    self.conn.send(message)
            except socket.error as msg:
                print("Socket error!: " +  str(msg))
                self.client.disconnect_from_server()
                self.running = False
        
class ClientThreadRecieve(Thread):
    def __init__(self,client,socket):
        super(ClientThreadRecieve, self).__init__()
        self.daemon = True
        self.running = True
        self.conn = socket
        self.client = client
    def stop(self):
        self.running = False
    def run(self):
        while self.running == True:
            try:
                data = self.conn.recv(9999999)
                if data:
                    if "_CONNECTVALID_" in data:
                        if data == "_CONNECTVALIDNOEDIT_":
                            self.client.approve_connection(False)
                        else:
                            self.client.approve_connection()
                    elif "_FULLDATA_" in data:
                        self.client.program.image.fromstring(data[10:])
                    elif "_KICK_" in data:
                        self.client.disconnect_from_server()
                    elif "_LOCK_" in data:
                        self.client.program.state = "STATE_MAIN_NOEDIT"
                    elif "_UNLOCK_" in data:
                        self.client.program.state = "STATE_MAIN"
                    elif "_CHATMESSAGE_" in data:
                        self.client.program.window_chat.display_message(data)
                    elif "_PIXELDATA_" in data:
                        self.client.program.image.process_thread.add(data)
                    elif "_BRUSHDATA_" in data:
                        self.client.program.image.process_thread.add(data)
                    elif "_MOUSEDATA_" in data:
                        self.client.program.image.process_thread.add(data)

                        
                    elif "_CONNECT_" in data:
                        li = parse_message(data,"_CONNECT_")
                        for i in li:
                            self.client.program.window_clients.add_client(i,self.client.program.font)
                        self.client.program.window_clients.sort_clients()
                            
                    elif "_DISCONNECT_" in data:
                        self.client.program.window_clients.remove_client(data[13:])
                        
            except socket.error as msg:
                print("Socket error!: " + str(msg))
                self.client.disconnect_from_server()
                self.running = False
        
class Client(object):
    def __init__(self,program):
        self.client_send = None
        self.client_recv = None
        self.connected = False
        self.connection_destination = ""
        self.username = ""
        self.server_pass = ""
        self.program = program

    def approve_connection(self,canEdit=True):
        self.connected = True
        if canEdit == True:
            self.program.state = "STATE_MAIN"
        else:
            self.program.state = "STATE_MAIN_NOEDIT"
        
    def connect_to_server(self,username,server,server_pass,admin=False):
        if username == "":
            return False
        if server == "":
            return False
        try:
            if self.connected == False:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection_destination = server
                if server.lower() == "localhost" or admin == True:
                    self.connection_destination = "127.0.0.1"

                self.username = username
                self.server_pass = server_pass
                if admin == True:
                    config = ConfigParser.RawConfigParser()
                    config.readfp(open('server.cfg'))
                    self.server_pass = config.get('ServerInfo', 'serverpass')

                client_socket.connect((self.connection_destination, 6121))

                
                self.client_send = ClientThreadSend(self,client_socket)
                self.client_send.start()
                self.client_recv = ClientThreadRecieve(self,client_socket)
                self.client_recv.start()
                
                self.send_message("_CONNECT_|" + self.username + "|" + self.server_pass)

                self.program.window_clients.add_client(username,self.program.font)
                self.program.window_chat.chat_field.set_name(username)
                self.program.window_chat.chat_field.set_maxchars(int(self.program.window_chat.width/self.program.font.size("X")[0]) - len(username)-2)
                self.program.window_chat.chat_field.set_pos((self.program.window_chat.pos[0] + self.program.window_chat.width/2,
                                                             self.program.window_chat.pos[1]+self.program.window_chat.height-self.program.window_chat.chat_field.font.size("X")[1]-4))


                
                sleep(0.5)

                self.send_message("_REQUESTIMAGE_")

                return True
            else:
                return False
        except Exception as e:
            print("Error: " + str(e))
            return False

    def disconnect_from_server(self,message=""):
        if self.connected == False:
            return
        self.send_message("_DISCONNECT_|" + self.username)
        self.program.window_clients.remove_client(self.username)
        self.client_send.stop()
        self.client_recv.stop()
        self.client_send = None
        self.client_recv = None
        self.connected = False
        self.program.state = "STATE_PROMPT"

        if message != "":
            pass
        print("Disconnecting client...")

    def send_message(self,message):
        if self.client_send is not None:
            if self.client_send.running == True:
                self.client_send.add(message)
