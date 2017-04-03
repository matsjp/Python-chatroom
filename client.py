import socket
import threading
import json

class ResponseHandler():
    def __init__(self):
        self.valid = ["error", "info", "message", "history"]

    def handle(self, payload):
        if payload["response"] not in self.valid:
            return
        else:
            if payload["response"] == "history":
                messageList = payload["content"]
                for i in range(len(messageList)):
                    temp = json.loads(messageList[i])
                    print(temp["sender"] + ": " + temp["content"])
                return
            print(payload["sender"] + ": " + payload["content"])

class RecieverThread(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.handler = ResponseHandler()

    def run(self):
        while True:
            msg = self.conn.recv(2048).decode()
            temp = json.loads(msg)
            self.handler.handle(temp)

class SenderThread(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn

    def run(self):
        while True:
            send = input("")
            if send.find(" ") != -1:
                request = send[:send.find(" ")]
                content = send[send.find(" ") + 1:]
            else:
                request = send
                content = None
            temp = {"request": request, "content": content}
            jsonObj = json.dumps(temp)
            self.conn.send(jsonObj.encode())

if __name__ == "__main__":
    host = socket.gethostname()
    port = 5555
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, port))
    recvThread = RecieverThread(clientSocket)
    recvThread.start()
    sendThread = SenderThread(clientSocket)
    sendThread.start()