import atexit
import ncsbench.common.socket as s
from ..common.ev3utils import init as ev3_dict_init

EV3 = None
MOTOR = None

def run(args):
    global EV3, MOTOR
    EV3=args.lib
    if args.type=="pistorms":
        print("unsupported platform: pistorms")
        print("\tstopping...")
        exit(1)
    m = EV3.MediumMotor(ev3_dict_init(args).motors[args.motor_port])
    if m.connected:
        global MOTOR
        MOTOR = m
    if not MOTOR:
        print("couldnt find Motor on port "+args.motor_port)
        print("\tstopping...")
        exit(1)
    MOTOR.polarity = 'inversed'
    atexit.register(stop_coast)
    args.sock.events[s.EVENTS.CRANE_STOP].always.add(lambda data:stop())
    args.sock.events[s.EVENTS.CRANE_UP].always.add(lambda data:up())
    args.sock.events[s.EVENTS.CRANE_DOWN].always.add(lambda data:down())
    args.sock.events[s.EVENTS.EXIT].always.add(lambda data:exit(0))

def stop():
    MOTOR.stop(stop_action='hold')

def up():
    MOTOR.run_forever(speed_sp=500, ramp_up_sp=10000)

def down():
    MOTOR.run_to_rel_pos(position_sp=-130, speed_sp=100, ramp_up_sp=0,stop_action='coast')

def stop_coast():
    MOTOR.stop(stop_action='coast')
