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
                                   args.sport, args.aport, args.cport),daemon=True).start()

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
        from ncsbench.robot import run
        run(args)

    def crn(args):
        client(args)
        from ncsbench.crane import run
        run(args)
    
    try:
        settings = json.load(open("settings.json", "r"))
    except FileNotFoundError:
        settings = {}
    default = {"verbose": False, "logging": False, "sport": 34543,
               "aport": 34544, "cport": 34545, "type": "ev3"}
    changed = False
    if not "port" in settings:
        settings["port"] = 5555
        changed = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=settings["port"])
    parser.add_argument("command", choices=["controller", "robot", "crane"])
    parser.add_argument("--override", action="store_true")
    args = parser.parse_known_args()
    if args[0].command == "controller":
        default = {"verbose": False, "logging": False,
                   "sport": 34543, "aport": 34544, "cport": 34545}
        for key in default:
            if not key in settings:
                settings[key] = default[key]
                changed = True
        parser = argparse.ArgumentParser()
        parser.add_argument("--verbose", type=bool,
                            choices=[True, False], default=settings["verbose"])
        parser.add_argument("--logging", type=bool,
                            choices=[True, False], default=settings["logging"])
        parser.add_argument("--sport", type=int, default=settings["sport"])
        parser.add_argument("--aport", type=int, default=settings["aport"])
        parser.add_argument("--cport", type=int, default=settings["cport"])
        a1,a2=args
        args=a2,a1
        args = parser.parse_args(*args)
        
    else:
        if "type" not in settings:
            settings["type"]="ev3"
            changed=True
        parser = argparse.ArgumentParser()
        parser.add_argument("--type")
        args = parser.parse_args(*args)
        
    if args.override:
        for key in settings:
            if key in args.__dict__:
                if not settings[key] == args.__dict__[key]:
                    settings[key] = args.__dict__[key]
                    changed = True
    if changed:
        json.dump(settings,open("settings.json","w"),indent=4)
    
    if args.command=="robot":
        rbt(args)
    elif args.command=="crane":
        crn(args)
    else:
        ctrl(args)


if __name__ == '__main__':
    main()
