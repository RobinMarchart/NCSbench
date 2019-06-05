#! /usr/bin/python3
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

def main():
    def ctrl(args):
        from threading import Thread
        Thread(target=serve, args=(args.port, args.verbose, args.logging,
                                   args.sport, args.aport, args.cport),daemon=False).start()
        from controller import main as m
        Thread(target=m,args=(args,)).start()

    def client(args):
        from importlib import import_module
        args.type = import_module("ev3dev."+args.type)
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
    
    try:
        settings = json.load(open("settings.json", "r"))
    except FileNotFoundError:
        settings = {}
    defaults ={
        "controller":(ctrl,{
            "--verbose":{"default":False,"type":int,"choices":["0","1"]},
            "--logging":{"default":False,"type":int,"choices":["0","1"]},
            "--sport":{"default":34543,"type":int},
            "--aport":{"default":34544,"type":int},
            "--cport":{"default":34545,"type":int},
            "--measurement_folder":{"default":".",'help':'Subfolder for measurements'},
            "--result_folder":{"default":".."}
        }),
        "robot":(rbt,{"--type":{"default":"ev3"}}),
        "crane":(crn,{"--type":{"default":"ev3"}})
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
    for key in a[1]:
        if (not key in settings) and ("default" in a[1][key]):
            settings[key]=a[1][key]["default"]
            changed=True
        else:
            a[1][key]["default"]=settings[key]
        parser.add_argument(key,**a[1][key])
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
    
    a[0](args)


if __name__ == '__main__':
    main()#TODO run as subprocess and relaunch after normal exit-> multi try run or maybe until x viable runs succeded, maybe also Stop Multicast at this level bat shutting down non controllers