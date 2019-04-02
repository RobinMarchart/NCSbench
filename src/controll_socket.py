import socket,struct,threading,enum,atexit

class SocketAlreadyExistsException(Exception):
	pass

EVENTS=enum.IntEnum('EVENTS','EXIT ERR INIT CRANE_UP CRANE_STOP CRANE_DOWN ROBOT_START ROBOT_STOP CONTINUE')
CLIENTS=enum.IntEnum('CLIENTS','ROBOT CRANE')
	
class Event:
	once=set()
	always=set()
	event=threading.Event()
	
	def __init__(self,event):
		self.event=event
	
	def wait(self):
		self.event.wait()
	def notice(self,data,addr,sock):
		self.event.set()
		for f in self.once:
			f(data,addr,sock)
		once=set()
		for f in self.always:
			f(data,addr,sock)
		self.event.clear()
		
class Client:
	def __init__(self,addr,sock):
		self.addr=addr
		self.sock=sock
		self.lock=threading.Lock()
		
class ControllSocket:
	def __init__(self):
		if "sock" in globals():
			raise SocketAlreadyExistsException()
		else:
			global sock
			sock=self
		self.sock=socket.socket()
		self.event=list()
		for x in EVENTS:
			self.event.append(Event(x))
			
	def _send(self,event,data,sock):
		if len(data)<2048:
			b=bytearray(struct.pack("!B",event))
			b.append(data)
			sock.send(b)
		else:
			x=len(data)-2047
			y=0
			while y<x:
				b=bytearray(struct.pack("!B",Eve.CONTINUE))
				b.append(data[y:y+2047])
				sock.send(b)
				y+=2047
			b=bytearray(struct.pack("!B",event))
			b.append(data[y:])
			sock.send(b)
			
	def recv(self,addr,sock):
		data=sock.recv(2048)
		type=struct.unpack("!B",data[0])
		if len(data>1):
			data=data[1:]
		else:
			data=bytes()
		if type==Event.CONTINUE:
			data=bytearray(data)
			while type==EVENTS.CONTINUE:
				datan=sock.recv(2048)
				type=struct.unpack("!B",datan[0])
				data.append(datan)
		self.event[type].notice(data,addr,self)
	
	def close(self):
		self.sock.close()
				
def _client_shutdown_hook(s):
	s.send(EVENTS.EXIT)	
	s.close()
			
class ClientSocket(ControllSocket):
	
	def __init__(self,controller):
		super().__init__()
		self.lock=threading.Lock()
		self.controller=controller
		self.sock.connect(self.controller)
		
		atexit.register(_client_shutdown_hook,self)
		def loop(self):
			while True:
				self.recv(self.controller,self.sock)
		
		threading.Thread(target=loop,args=(self,),daemon=True).start()
		
		def shutdown(data,addr,sock):
			atexit.unregister(_client_shutdown_hook)
			sock.close()
			exit()
		
		self.event[EVENTS.EXIT].always.add(shutdown)
		
	def send(self, event,data=b''):
		self.lock.acquire()
		self._send(event,data,self.sock)
		self.lock.release()
	
	def init(self,client_type):
		self.send(EVENTS.INIT,struct.pack('!B',client_type))
		

	
class RobotSocket(ClientSocket):
	def __init__(self,controller):
		super().__init__(controller)
		
		self.init(CLIENTS.ROBOT)
		
class CraneSocket(ClientSocket):
	def __init__(self,controller,crane):
		super()._init__(controller)
		self.crane=crane
		self.init(CLIENTS.CRANE)
		def up(data,addr,self):
			self.crane.up()
		self.event[EVENTS.CRANE_UP].always.add(up)
		def stop(data,addr,sock):
			sock.crane.stop()
		sock.event[EVENTS.CRANE_STOP].always.add(stop)
		def down(data,addr,sock):
			sock.crane.down()
		sock.event[EVENTS.CRANE_DOWN].always.add(down)
		
def _controller_shutdown_hook(s):
	for client in s.clients:
		s.send(EVENTS.EXIT)
	s.close()
	
class ControllerSocket(ControllSocket):
	def __init__(self,cport):
		super().__init__()
		self.sock.bind(("",cport))
		self.sock.listen()
		self.clients=dict()
		self.types=[len(CLIENTS)]
		def recv_loop(sock,client):
			while True:
				sock.recv(client.addr,client.sock)
				
		def accept_loop(sock):
			while True:
				c=Client(*sock.sock.accept())
				self.clients[c.addr]=c
				threading.Thread(target=recv_loop,args=(sock,c),daemon=True).start()
				
		threading.Thread(target=accept_loop,args=(self,),daemon=True).start()
		
		atexit.register( _controller_shutdown_hook,self)
		
		def shutdown(data,addr,sock):
			atexit.unregister(_controller_shutdown_hook)
			for client in sock.clients:
				if not client.addr==addr:
					sock.send(EVENTS.EXIT,client)
			sock.close()
			exit()
		
		self.event[EVENTS.EXIT].always.add(shutdown)
		
		def init(data,addr,sock):
			t=struct.unpack('!B',data)
			c=sock.clients[addr]
			sock.types[t]=c
			c.type=t
		
		self.event[EVENTS.INIT].always.add(init)
		
	def close(self):
		super().close()
		for client in self.clients:
			client.sock.close()
	
	def send(self,event,client,data=b''):
		client.lock.acquire()
		self._send(event,data,client.sock)
		client.lock.release()
		
