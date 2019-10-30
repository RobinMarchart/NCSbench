
import socket as b_socket
import struct
import argparse
import time
import json
import multiprocessing
import pathlib
import os
import atexit
import ncsbench.common.socket as com_socket
# verbose logging (copy_logfile) sport aport cport runtime runs
PACK_FORMAT = '!2?5I'


def rcv(port):
    client = b_socket.socket(b_socket.AF_INET, b_socket.SOCK_DGRAM)  # UDP
    client.setsockopt(b_socket.SOL_SOCKET, b_socket.SO_BROADCAST, 1)
    client.bind(("", port))
    while True:
        data, addr = client.recvfrom(1024)
        return (addr, struct.unpack(PACK_FORMAT, data))

#   const int  bool    bool    int   int   int int int


def main(debugging=False):
    defaults = {
        "controller": {
            "--verbose": {"default": False, "type": int, "choices": ["0", "1"]},
            "--logging": {"default": False, "type": int, "choices": ["0", "1"]},
            "--sport": {"default": 34543, "type": int},
            "--aport": {"default": 34544, "type": int},
            "--cport": {"default": 34545, "type": int},
            "--measurement_folder": {"default": ".", 'help': 'Subfolder for measurements'},
            "--result_folder": {"default": ".."},
            "--port": {"default": 5555, "type": int},
            # "--no-crane":{"action":"store_true"},
            "runs": {"default": 1, "type": int},
            "runtime": {"default": 120, "type": int}
        },
        "robot": {
            "--type": {"default": "ev3"},
            "--port": {"default": 5555, "type": int},
            "--motor_l_port": {"default": "B", "choices": ["A", "B", "C", "D"]},
            "--motor_r_port": {"default": "A", "choices": ["A", "B", "C", "D"]},
            "--touch_1_port": {"default": "1", "choices": ["1", "2", "3", "4"]},
            "--touch_2_port": {"default": "2", "choices": ["1", "2", "3", "4"]},
            "--gyro_port": {"default": "4", "choices": ["1", "2", "3", "4"]}
        },
        "crane": {
            "--type": {"default": "ev3"},
            "--port": {"default": 5555, "type": int},
            "--motor_port": {"default": "A", "choices": ["A", "B", "C", "D"]}},
        # "--manual": {"action":"store_true"}
    }
    try:
        settings = json.load(open(os.path.expanduser("~/.NCSbench.json"), "r"))
    except FileNotFoundError:
        settings = {}
        for key in defaults:
            settings[key] = {}
    changed = False
    for k in defaults:
        a = defaults[k]
        for key in a:
            if (not key in settings[k]) and ("default" in a[key]):
                settings[k][key] = a[key]["default"]
                changed = True
            else:
                a[key]["default"] = settings[k][key]
    parser = argparse.ArgumentParser()
    parser.add_argument("--override", action="store_true")
    subparsers = parser.add_subparsers(required=True, dest="cmd")
    for k in settings:
        if not k in []:
            p = subparsers.add_parser(k)
            for parse in settings[k]:
                p.add_argument(parse, **defaults[k][parse])
    args = parser.parse_args()

    if args.override:
        for key in settings:
            if key in args.__dict__:
                if not settings[key] == args.__dict__[key]:
                    settings[key] = args.__dict__[key]
                    changed = True
    if changed:
        path = pathlib.Path(os.path.expanduser("~/.NCSbench.json"))
        path.open("a").close()
        json.dump(settings, path.open("w"), indent=4)

    if args.cmd == "controller":
        server = b_socket.socket(
            b_socket.AF_INET, b_socket.SOCK_DGRAM, b_socket.IPPROTO_UDP)
        server.setsockopt(b_socket.SOL_SOCKET, b_socket.SO_BROADCAST, 1)
        server.settimeout(0.2)
        server.bind(("", args.port+1))
        message = struct.pack(PACK_FORMAT, args.verbose,
                              args.logging, args.sport, args.aport, args.cport, args.runs, args.runtime)
        import threading

        # send via broadcast
        def broadcast_send(server, message, port, event):
            with server:
                while not event.is_set():
                    server.sendto(message, ('<broadcast>', port))
                    time.sleep(1)

        event = threading.Event()

        broadcast = threading.Thread(
            target=broadcast_send, args=(server, message, args.port, event))

        con_socket = com_socket.ControllerSocket(
            args.cport, args.result_folder, event)
        del event, server, message
        broadcast.start()
        broadcast.join()
        del broadcast

        args.address = con_socket.addresses[com_socket.CLIENTS.ROBOT].addr
        from ncsbench.controller import main as controller_main

        class ExitHook:
            indicator = True
            worker = None

            def unusable_exit(self):
                if worker:
                    self.indicator = False
                    self.worker.kill()
        exH = ExitHook()
        con_socket.event[com_socket.EVENTS.EXIT].always.add(
            lambda data, addr, sock: int.from_bytes(data) or exH.unusable_exit())
        for x in range(args.runs):
            worker = multiprocessing.Process(
                target=controller_main, args=(args, con_socket.queue_I, con_socket.queue_O, debugging))
            exH.indicator = True
            exH.worker = worker
            con_socket.ready[0].wait()
            con_socket.ready[0].clear()
            worker.start()
            def f(): return worker.kill()
            atexit.register(f)
            worker.join()
            atexit.unregister(f)
            exH.worker = None
            if worker.exitcode != 0:
                print("error in subprocess")
                print("\tstopping...")

                exit(1)
            if exH.indicator:
                pass  # TODO collect logs

        con_socket.send(com_socket.EVENTS.ERR, com_socket.CLIENTS.ROBOT)
        con_socket.send(com_socket.EVENTS.ERR, com_socket.CLIENTS.CLIENT)
    else:
        from importlib import import_module
        import ncsbench.common.ev3utils as args_lib
        args.lib = args_lib
        args.lib.init(args.type)
        addr, d = rcv(args.port)
        args.address = addr[0]
        verbose, logging, sport, aport, cport, runs, runtime = d
        args.verbose = verbose
        args.logging = logging
        args.sport = sport
        args.aport = aport
        args.cport = cport
        args.runtime=runtime
        if args.cmd == "robot":
            con_socket = com_socket.RobotSocket((args.address, args.cport))

            def run_robot(args, queue_I, queue_O):
                args.sock = com_socket.ClientWorkerReceiver(queue_I, queue_O)
                from ncsbench.robot import run
                run(args)
            con_socket.init()
            while True:
                process = multiprocessing.Process(target=run_robot, args=(
                    args, con_socket.queue_I, con_socket.queue_O))
                process.start()
                process.join()
                if process.exitcode != 0:
                    con_socket.send(com_socket.EVENTS.EXIT,
                                    process.exitcode.to_bytes())

        elif args.cmd == "crane":
            con_socket = com_socket.CraneSocket((args.address, args.cport))

            def run_crane(args, queue_I, queue_O):
                args.sock = com_socket.ClientWorkerReceiver(queue_I, queue_O)
                from ncsbench.crane import run
                run(args)
            con_socket.init()
            while True:
                process = multiprocessing.Process(target=run_crane, args=(
                    args, con_socket.queue_I, con_socket.queue_O))
                process.start()
                process.join()
