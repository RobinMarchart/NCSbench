
import socket
import struct
import argparse
import time
import json
# verbose logging (copy_logfile) sport aport cport
PACK_FORMAT = '!2?3I'


def rcv(port):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(("", port))
    while True:
        data, addr = client.recvfrom(1024)
        return (addr, struct.unpack(PACK_FORMAT, data))

#   const int  bool    bool    int   int   int


def serve(port, verbose, logging, sport, aport, cport):
    server = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.settimeout(0.2)
    server.bind(("", port+1))
    message = struct.pack(PACK_FORMAT, verbose, logging, sport, aport, cport)
    while True:
        server.sendto(message, ('<broadcast>', port))
        time.sleep(10)
def ctrl(args):
    from threading import Thread
    Thread(target=serve, args=(args.port, args.verbose, args.logging,
                               args.sport, args.aport, args.cport),daemon=False).start()
    from controller import main as m
    Thread(target=m,args=(args,)).start()

def client(args):
    from importlib import import_module
    args.lib = import_module("ev3dev."+args.type)
    addr, d = rcv(args.port)
    args.address = addr[0]
    verbose, logging, sport, aport, cport = d
    args.verbose = verbose
    args.logging = logging
    args.sport = sport
    args.aport = aport
    args.cport = cport

def rbt(args):
    client(args)
    from robot import run
    run(args)

def crn(args):
    client(args)
    from crane import run
    run(args)

def main():
    try:
        settings = json.load(open("settings.json", "r"))
    except FileNotFoundError:
        settings = {}
    defaults ={
        "controller":{
            "--verbose":{"default":False,"type":int,"choices":["0","1"]},
            "--logging":{"default":False,"type":int,"choices":["0","1"]},
            "--sport":{"default":34543,"type":int},
            "--aport":{"default":34544,"type":int},
            "--cport":{"default":34545,"type":int},
            "--measurement_folder":{"default":".",'help':'Subfolder for measurements'},
            "--result_folder":{"default":".."}
        },
        "robot":{"--type":{"default":"ev3"},
            "--motor_l_port":{"default":"B","choices":["A","B","C","D"]},
            "--motor_r_port":{"default":"A","choices":["A","B","C","D"]},
            "--touch_1_port":{"default":"1","choices":["1","2","3","4"]},
            "--touch_2_port":{"default":"2","choices":["1","2","3","4"]},
            "--gyro_port":{"default":"4","choices":["1","2","3","4"]}
            },
        "crane":{"--type":{"default":"ev3"},
            "--motor_port":{"default":"A","choices":["A","B","C","D"]}}
    }
    changed = False
    if not "port" in settings:
        settings["port"] = 5555
        changed = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings["port"])
    parser.add_argument("command", choices=defaults)
    parser.add_argument("--override", action="store_true")
    args = parser.parse_known_args()
    a1,a2=args
    a=defaults[a1.command]
    parser=argparse.ArgumentParser()
    for key in a:
        if (not key in settings) and ("default" in a[key]):
            settings[key]=a[key]["default"]
            changed=True
        else:
            a[key]["default"]=settings[key]
        parser.add_argument(key,**a[key])
    args=a2,a1
    args = parser.parse_args(*args)
        
    
    if args.override:
        for key in settings:
            if key in args.__dict__:
                if not settings[key] == args.__dict__[key]:
                    settings[key] = args.__dict__[key]
                    changed = True
    if changed:
        json.dump(settings,open("settings.json","w"),indent=4)
    
    if args.command =="controller":
        server = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.settimeout(0.2)
        server.bind(("", args.port+1))
        message = struct.pack(PACK_FORMAT, args.verbose, args.logging, args.sport, args.aport, args.cport)
        import threading
        revent=threading.Event()
        cevent=threading.Event()
        
        #send via broadcast
        server.sendto(message, ('<broadcast>', args.port))
    else:
        pass


