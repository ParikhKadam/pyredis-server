import threading
import SocketServer
import operation

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        s = self.request
        f = s.makefile()
        count = f.readline()
        if count.startswith("*"):
            count = int(count[1:].strip())
            print count
            paras = []
            for x in range(count):
                length = f.readline()
                if length.startswith("$"):
                    length = int(length[1:].strip())
                    value = f.read(length)
                    f.read(2)  # skip CR LF
                    print length, value
                    paras.append(value)
                else:
                    print length
            f.write("\r\n".join(operation.handle_req(paras)))

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class redis_server:
    def __init__(self, HOST, PORT=6379):
        self.HOST = HOST
        self.PORT = PORT
        self.server = None

    def start(self):
        self.server = ThreadedTCPServer((self.HOST, self.PORT), ThreadedTCPRequestHandler)
        ip, port = self.server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=self.server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print "Server loop running in thread:", server_thread.name

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None