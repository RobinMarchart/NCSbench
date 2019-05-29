import atexit
import enum
import socket
import threading
import traceback
import struct
import pathlib

class SocketAlreadyExistsException(Exception):
    pass


EVENTS = enum.IntEnum(
    'EVENTS', 'EXIT ERR INIT CRANE_UP CRANE_STOP CRANE_DOWN ROBOT_CALLIB ROBOT_START ROBOT_STOP CONTINUE')
CLIENTS = enum.IntEnum('CLIENTS', 'ROBOT CRANE')


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


class ControllSocket:
    def __init__(self):
        if "sock" in globals():
            raise SocketAlreadyExistsException()
        else:
            global sock
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
    s.send(EVENTS.EXIT)
    s.close()
#TODO exit on connection lost - ping continuesly


class ClientSocket(ControllSocket):

    def __init__(self, controller,daemon):
        super().__init__()
        self.lock = threading.Lock()
        self.controller = controller
        self.sock.connect(self.controller)

        atexit.register(_client_shutdown_hook, self)

        def loop(self):
            while True:
                self.recv(self.controller, self.sock)

        threading.Thread(target=loop, args=(self,), daemon=daemon).start()

        def shutdown(data, addr, sock):
            atexit.unregister(_client_shutdown_hook)
            sock.close()
            exit()

        self.event[EVENTS.EXIT].always.add(shutdown)

    def send(self, event, data=b''):
        with self.lock:
            self._send(event, data, self.sock)

    def init(self, client_type):
        self.send(EVENTS.INIT, bytes(client_type))


class RobotSocket(ClientSocket):
    def __init__(self, controller,daemon=True):
        super().__init__(controller)

    def init(self):
        super().init(CLIENTS.ROBOT)
    def unregister_shutdown(self):
        atexit.unregister(_client_shutdown_hook)


class CraneSocket(ClientSocket):
    def __init__(self, controller,daemon=True):
        super().__init__(controller)
        import ncsbench.crane as crane

        def up(data, addr, self):
            crane.up()
        self.event[EVENTS.CRANE_UP].always.add(up)

        def stop(data, addr, sock):
            crane.stop()
        sock.event[EVENTS.CRANE_STOP].always.add(stop)

        def down(data, addr, sock):
            crane.down()
        sock.event[EVENTS.CRANE_DOWN].always.add(down)

    def init(self):
        super().init(CLIENTS.CRANE)


def _controller_shutdown_hook(s):
    for client in s.clients:
        print(client)
        s.send(EVENTS.EXIT, client)
    s.close()


class ControllerSocket(ControllSocket):
    def __init__(self, cport,r_event:threading.Event,c_event:threading.Event,result_folder):
        super().__init__()
        self.sock.bind(("", cport))
        self.sock.listen()
        self.clients = dict()
        self.types = [len(CLIENTS)]
        self.r_event=r_event
        self.c_event=c_event
        self.result_folder=result_folder

        def recv_loop(sock, client):
            while True:
                sock.recv(client.addr, client.sock)

        def accept_loop(sock):
            while True:
                c = Client(*sock.sock.accept())
                sock.clients[c.addr] = c
                threading.Thread(target=recv_loop, args=(
                    sock, c), daemon=True).start()

        threading.Thread(target=accept_loop, args=(self,), daemon=True).start()

        atexit.register(_controller_shutdown_hook, self)

        def shutdown(data, addr, sock):
            atexit.unregister(_controller_shutdown_hook)
            for client in sock.clients:
                if not client.addr == addr:
                    sock.send(EVENTS.EXIT, client)
            sock.close()
            exit()

        self.event[EVENTS.EXIT].always.add(shutdown)

        def init(data, addr, sock):
            t = data[0]
            c = sock.clients[addr]
            sock.types[t] = c
            c.type = t
            if t==CLIENTS.ROBOT:
                sock.r_event.set()
            else:
                sock.c_event.set()

        self.event[EVENTS.INIT].always.add(init)

            

    def close(self):
        super().close()
        for client in self.clients:
            client.sock.close()

    def send(self, event, client, data=b''):
        with client.lock:
            self._send(event, data, client.sock)
