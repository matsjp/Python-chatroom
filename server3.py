# -*- coding: utf-8 -*-
import socketserver
import json
from datetime import datetime
import socket
"""
Variables and functions that must be used by all the ClientHandler objects
must be written here (e.g. a dictionary for connected clients)
"""
connections = {}
messageList = []

class ClientHandler(socketserver.BaseRequestHandler):
    """
    This is the ClientHandler class. Everytime a new client connects to the
    server, a new ClientHandler object will be created. This class represents
    only connected clients, and not the server itself. If you want to write
    logic for the server, you must write it outside this class
    """

    def handle(self):
        """
        This method handles the connection between a client and the server.
        """
        self.connection = self.request
        self.validRequests = {"login": self.loginHandler, "logout": self.logoutHandler, "msg": self.msgHandler,
                              "names": self.namesHandler, "help": self.helpHandler, "whisper": self.whisperHandler}
        connections.update({self.connection: None})
        self.confirmConnection(self.connection)

        # Loop that listens for messages from the client
        while True:
            try:
                received_string = self.connection.recv(4096).decode()
                payload = json.loads(received_string)
                request = payload["request"]
                if request not in self.validRequests:
                    sender = "server"
                    response = "error"
                    content = "Invalid command, please type help for full list of valid commands"
                    jsonSend = json.dumps(
                        {"timestamp": self.getTimestamp(), "sender": sender, "response": response, "content": content})
                    self.connection.send(jsonSend.encode())
                else:
                    self.validRequests[request](payload, self.connection)
            except:
                print("stop")
                del connections[self.connection]
                break


            # TODO: Add handling of received payload from client
    def loginHandler(self, payload, conn):
        sender = "server"
        timeStamp = self.getTimestamp()
        if self.checkLogin(conn):
            response = "error"
            content = "You are already logged in"
            jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
            conn.send(jsonSend.encode())
            return
        elif not self.validateUsername(payload["content"]):
            response = "error"
            content = "Invalid username"
            jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
            conn.send(jsonSend.encode())
            return
        elif not self.availableUsername(payload["content"]):
            response = "error"
            content = "Username is already taken"
            jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
            conn.send(jsonSend.encode())
        else:
            connections[conn] = payload["content"]
            response = "info"
            content = "You are now logged in"
            jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
            conn.send(jsonSend.encode())
            if len(messageList) > 0:
                response = "history"
                content = messageList
                print(content)
                jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
                conn.send(jsonSend.encode())

    def whisperHandler(self, payload, conn):
        if self.checkLogin(conn):
            timeStamp = self.getTimestamp()
            if payload["content"].find(" ") == -1:
                sender = "server"
                response = "error"
                content = "Whisper command error. The correct format is: whisper name message"
                jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
                conn.send(jsonSend.encode())
            else:
                name = payload["content"][:payload["content"].find(" ")]
                names = connections.values()
                if name not in names:
                    sender = "server"
                    response = "error"
                    content = "No user with that name"
                    jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
                    conn.send(jsonSend.encode())
                else:
                    message = payload["content"][payload["content"].find(" ") + 1:]
                    sender = connections[conn]
                    keys = connections.keys()
                    for key in keys:
                        if connections[key] == name:
                            recieverConn = key
                    response = "message"
                    contentTo = "Whisper to " + name + ": " + message
                    contentFrom = "Whisper from " + sender + ": " + message
                    jsonSendTo = json.dumps({"timestamp": timeStamp, "sender": "server", "response": response, "content": contentTo})
                    conn.send(jsonSendTo.encode())
                    jsonSendFrom = json.dumps({"timestamp": timeStamp, "sender": "server", "response": response, "content": contentFrom})
                    recieverConn.send(jsonSendFrom.encode())
        else:
            self.sendLoginMessage()

    def logoutHandler(self, payload, conn):
        if self.checkLogin(conn):
            timeStamp = self.getTimestamp()
            connections[conn] = None
            sender = "server"
            response = "info"
            content = "You are now logged out"
            jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
            conn.send(jsonSend.encode())
        else:
            self.sendLoginMessage(conn)

    def msgHandler(self, payload, conn):
        if self.checkLogin(conn):
            timeStamp = self.getTimestamp()
            sender = connections[conn]
            message = payload["content"]
            response = "message"
            content = message
            d = {"timestamp": timeStamp, "sender": sender, "response": response, "content": content}
            jsonSend = json.dumps(d)
            keys = connections.keys()
            messageList.append(json.dumps(d))
            for key in keys:
                if connections[key] is not None:
                    key.send(jsonSend.encode())
        else:
            self.sendLoginMessage(conn)

    def namesHandler(self, payload, conn):
        if self.checkLogin(conn):
            timeStamp = self.getTimestamp()
            temp = connections.values()
            namesList = []
            for name in temp:
                if name is not None:
                    namesList.append(name)
            nameString = ""
            for name in namesList:
                nameString += name + ", "
            content = "The names of all users are: " + nameString[:len(nameString) - 2]
            sender = "server"
            response = "info"
            jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
            conn.send(jsonSend.encode())
        else:
            self.sendLoginMessage(conn)

    def helpHandler(self, payload, conn):
        timeStamp = self.getTimestamp()
        sender = "server"
        response = "info"
        s = "The following requests are legal: "
        keyList = self.validRequests.keys()
        for request in keyList:
            s += request + ", "
        s = s[:len(s) - 2]
        content = s
        jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
        conn.send(jsonSend.encode())

    def confirmConnection(self, conn):
        timeStamp = self.getTimestamp()
        sender = "server"
        response = "info"
        content = "Connection established"
        jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
        conn.send(jsonSend.encode())

    def sendLoginMessage(self, conn):
        timeStamp = self.getTimestamp()
        sender = "server"
        response = "error"
        content = "You need to log in to do that"
        jsonSend = json.dumps({"timestamp": timeStamp, "sender": sender, "response": response, "content": content})
        conn.send(jsonSend.encode())

    def validateUsername(self, s):
        valid = True
        validChars = "1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm"
        for c in s:
            if c not in validChars:
                valid = False
        return valid

    def checkLogin(self, conn):
        return connections[conn] is not None

    def availableUsername(self, s):
        usernames = connections.values()
        for username in usernames:
            if s == username:
                return False
        return True

    def getTimestamp(self):
        return datetime.now().strftime("%d/%m/%y %H:%M:%S")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    This class is present so that each client connected will be ran as a own
    thread. In that way, all clients will be served by the server.

    No alterations are necessary
    """
    allow_reuse_address = True


if __name__ == "__main__":
    """
    This is the main method and is executed when you type "python Server.py"
    in your terminal.

    No alterations are necessary
    """
    HOST, PORT = socket.gethostname(), 5555
    print('Server running...')

    # Set up and initiate the TCP server
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    server.serve_forever()
