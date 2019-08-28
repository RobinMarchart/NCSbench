
import socket
import struct
import argparse
import time
import json
import multiprocessing
import pathlib
import os
import ncsbench.common.socket as com_socket
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

def main(debugging=False):
    defaults ={
        "controller":{
            "--verbose":{"default":False,"type":int,"choices":["0","1"]},
            "--logging":{"default":False,"type":int,"choices":["0","1"]},
            "--sport":{"default":34543,"type":int},
            "--aport":{"default":34544,"type":int},
            "--cport":{"default":34545,"type":int},
            "--measurement_folder":{"default":".",'help':'Subfolder for measurements'},
            "--result_folder":{"default":".."},
            "--port":{"default":5555,"type":int},
            "runs":{"default":1,"type":int}
        },
        "robot":{"--type":{"default":"ev3"},
            "--port":{"default":5555,"type":int},
            "--motor_l_port":{"default":"B","choices":["A","B","C","D"]},
            "--motor_r_port":{"default":"A","choices":["A","B","C","D"]},
            "--touch_1_port":{"default":"1","choices":["1","2","3","4"]},
            "--touch_2_port":{"default":"2","choices":["1","2","3","4"]},
            "--gyro_port":{"default":"4","choices":["1","2","3","4"]}
            },
        "crane":{"--type":{"default":"ev3"},
            "--port":{"default":5555,"type":int},
            "--motor_port":{"default":"A","choices":["A","B","C","D"]}}
    }
    try:
        settings = json.load(open(os.path.expanduser("~/.NCSbench.json"), "r"))
    except FileNotFoundError:
        settings = {}
        for key in defaults:
            settings[key]={}
    changed = False
    for k in defaults:
        a=defaults[k]
        for key in a:
            if (not key in settings[k]) and ("default" in a[key]):
                settings[k][key]=a[key]["default"]
                changed=True
            else:
                a[key]["default"]=settings[k][key]
    parser = argparse.ArgumentParser()
    parser.add_argument("--override", action="store_true")
    subparsers = parser.add_subparsers(required=True,dest="cmd")
    for k in settings:
        if not k in []:
            p=subparsers.add_parser(k)
            for parse in settings[k]:
                p.add_argument(parse,**defaults[k][parse])
    args = parser.parse_args()
    
    if args.override:
        for key in settings:
            if key in args.__dict__:
                if not settings[key] == args.__dict__[key]:
                    settings[key] = args.__dict__[key]
                    changed = True
    if changed:
        path=pathlib.Path(os.path.expanduser("~/.NCSbench.json"))
        path.open("a").close()
        json.dump(settings,path.open("w"),indent=4)
    
    if args.cmd =="controller":
        server = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.settimeout(0.2)
        server.bind(("", args.port+1))
        message = struct.pack(PACK_FORMAT, args.verbose, args.logging, args.sport, args.aport, args.cport)
        import threading
        revent=threading.Event()
        
        #send via broadcast
        def broadcast_send(server,message,port):
            server.sendto(message, ('<broadcast>', port))
        broadcast=threading.Thread(target=broadcast_send,args=(server,message,args.port))

        event=threading.Event()

        con_socket=com_socket.ControllerSocket(args.cport,args.result_folder,event)

        event.wait()
        del event

        from ncsbench.controller import main as controller_main
        for x in range(args.runs):
            worker=multiprocessing.Process(target=controller_main,args=(args,con_socket.queue,debugging))
            worker.start()
            worker.join()
        con_socket.send(com_socket.EVENTS.ERR,com_socket.CLIENTS.ROBOT)
        con_socket.send(com_socket.EVENTS.ERR,com_socket.CLIENTS.CLIENT)
    else:
        pass


