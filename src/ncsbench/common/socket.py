import atexit
import enum
import socket
import threading
import traceback
import struct
import pathlib
import typing
import multiprocessing
class SocketAlreadyExistsException(Exception):
    pass


EVENTS = enum.IntEnum(
    'EVENTS', 'EXIT ERR INIT CRANE_UP CRANE_STOP CRANE_DOWN ROBOT_CALLIB ROBOT_START ROBOT_STOP CONTINUE')
CLIENTS = enum.IntEnum('CLIENTS', 'ROBOT CRANE')

class ClientMessage:
    def __init__(self, event_type:EVENTS, message):
        self.type=event_type
        self.message=message

class ControllerMessage:
    def __init__(self, event_type:EVENTS, message, client:CLIENTS):
        self.type=event_type
        self.message=message
        self.client=client

class Event:

    def __init__(self, num):
        self.num = num
        self.once = set()
        self.always = set()
        self.event = threading.Event()

    def wait(self):
        self.event.wait()

    def notice(self, data, addr, sock):
        self.event.set()
        for f in self.once:
            f(data, addr, sock)
        once = set()
        for f in self.always:
            f(data, addr, sock)
        self.event.clear()


class Client:
    def __init__(self, sock, addr):
        self.addr = addr
        self.sock = sock
        self.lock = threading.Lock()

sock=None

class ControllSocket:
    def __init__(self):
        global sock
        if sock:
            raise SocketAlreadyExistsException()
        else:
            sock = self
        self.sock = socket.socket()
        self.event = list()
        for x in EVENTS:
            while(x > len(self.event)):
                self.event.append(None)
            self.event.append(Event(x))

    def _send(self, event, data, sock):
        if len(data) < 2048:
            b = bytearray(event.value)
            b.extend(data)
            sock.send(b)
        else:
            x = len(data)-2047
            y = 0
            while y < x:
                b = bytearray(EVENTS.CONTINUE)
                b.extend(data[y:y+2047])
                sock.send(b)
                y += 2047
            b = bytearray(event)
            b.extend(data[y:])
            sock.send(b)

    def handle_incomeing(self, data, addr, event_type):
        pass

    def recv(self, addr, sock):
        try:
            data = sock.recv(2048)
            while len(data) < 1:
                data = sock.recv(2048)
            type = data[0]
            if len(data) > 1:
                data = data[1:]
            else:
                data = bytes()
            if type == EVENTS.CONTINUE:
                data = bytearray(data)
                while type == EVENTS.CONTINUE:
                    datan = sock.recv(2048)
                    type = datan[0]
                    data.extend(datan[1:])
            self.event[type].notice(data, addr, self)

        except Exception:
            traceback.print_exc()

    def close(self):
        self.sock.close()


def _client_shutdown_hook(s):
    s.send(EVENTS.ERR)
    s.close()
#TODO exit on connection lost - ping continuesly


class ClientSocket(ControllSocket):

    def __init__(self, controller,daemon):
        super().__init__()
        self.lock = threading.Lock()
        self.controller = controller
        self.sock.connect(self.controller)
        self.queue_O=multiprocessing.Queue()
        self.queue_I=multiprocessing.Queue()

        atexit.register(_client_shutdown_hook, self)

        def loop(self):
            while True:
                self.recv(self.controller, self.sock)

        threading.Thread(target=loop, args=(self,), daemon=daemon).start()

        def shutdown(data, addr, sock):
            atexit.unregister(_client_shutdown_hook)
            sock.close()
            exit()

        self.event[EVENTS.ERR].always.add(shutdown)
        def client_loop(q,s):
            while True:
                e=q.get()
                s.send(e.type,e.message)
                if(e.type==EVENTS.ERR):
                    print("error in subprocess")
                    print("\tstopping...")
                    exit(1)
        threading.Thread(target=client_loop,args=(self.queue_O,self),daemon=True)
    
    def handle_incomeing(self, data, addr, event_type):
        self.queue_I.put(ClientMessage(event_type,data))

    def send(self, event, data=b''):
        with self.lock:
            self._send(event, data, self.sock)

    def init(self, client_type):
        self.send(EVENTS.INIT, bytes(client_type))


class RobotSocket(ClientSocket):
    def __init__(self, controller,daemon=True):
        super().__init__(controller,daemon)

    def init(self):
        super().init(CLIENTS.ROBOT)
    def unregister_shutdown(self):
        atexit.unregister(_client_shutdown_hook)


class CraneSocket(ClientSocket):
    def __init__(self, controller,daemon=True):
        super().__init__(controller,daemon)

    def init(self):
        super().init(CLIENTS.CRANE)


def _controller_shutdown_hook(s):
    for client in s.clients:
        print(client)
        s.send(EVENTS.EXIT, client)
    s.close()


class ControllerSocket(ControllSocket):
    def __init__(self, cport,result_folder,connected:threading.Event):
        super().__init__()
        self.sock.bind(("", cport))
        self.sock.listen()
        self.clients = dict()
        self.addresses=[]
        self.result_folder=result_folder
        self.queue_I=multiprocessing.Queue()
        self.queue_O=multiprocessing.Queue()
        self.connected=connected

        def recv_loop(sock, client):
            while True:
                sock.recv(client.addr, client.sock)

        def accept_loop(sock):
            while True:
                c = Client(*sock.sock.accept())
                sock.clients[c.addr] = c
                threading.Thread(target=recv_loop, args=(
                    sock, c), daemon=True).start()

        atexit.register(_controller_shutdown_hook, self)

        def shutdown_err(data, addr, sock):
            atexit.unregister(_controller_shutdown_hook)
            for client in sock.clients:
                if not client.addr == addr:
                    sock.send(EVENTS.EXIT, client)
            sock.close()
            exit(1)

        self.event[EVENTS.ERR].always.add(shutdown_err)

        def init(data, addr, sock):
            t = data[0]
            c = sock.clients[addr]
            sock.addresses.insert(t,addr)
            c.type = t
            if len(self.addresses)==len(CLIENTS):
                self.connected.set()
                del self.connected

        self.event[EVENTS.INIT].always.add(init)

        threading.Thread(target=accept_loop, args=(self,), daemon=True).start()

        def client_loop(q,s):
            while True:
                e=q.get()
                s.send(e.type,e.client,e.message)
                if(e.type==EVENTS.ERR):
                    print("error in subprocess")
                    print("\tstopping...")
                    exit(1)
        threading.Thread(target=client_loop,args=(self.queue_O,self),daemon=True)

    def handle_incomeing(self, data, addr, event_type):
        self.queue_I.put(ControllerMessage(event_type,data,self.clients[addr].type))

    def close(self):
        super().close()
        for client in self.clients:
            client.sock.close()

    def send(self, event, client, data=b''):
        with client.lock:
            self._send(event, data, client.sock)

class ReceiverEvent:

    def __init__(self, num):
        self.num = num
        self.once = set()
        self.always = set()
        self.event = threading.Event()

    def wait(self):
        self.event.wait()

    def notice(self, data):
        self.event.set()
        for f in self.once:
            f(data)
        once = set()
        for f in self.always:
            f(data)
        self.event.clear()

class ClientWorkerReceiver:
    def __init__(self, queue_I,queue_O):
        self.queue_I=queue_I
        self.queue_O=queue_O
        self.events=[ReceiverEvent(e)for e in list(EVENTS)]
        def f(q,e):
            while True:
                n=q.get()
                e[n.type].notice(e.message)
        threading.Thread(target=f,args=(self.queue_I,self.events))

    def send(self,event_type,message):
        self.queue_O.put(ClientMessage(event_type,message))

class ControllerWorkerReceiver:
    def __init__(self, queue_I,queue_O):
        self.queue_I=queue_I
        self.queue_O=queue_O
        self.events=[[ReceiverEvent(e)for e in list(EVENTS)]for c in list(CLIENTS)]
        def f(q,e):
            while True:
                n=q.get()
                e[n.client][n.type].notice(e.message)
        threading.Thread(target=f,args=(self.queue_I,self.events),daemon=True).start()
    
    def send(self,event_type,message,client):
        self.queue_O.put(ControllerMessage(event_type,message,client))
