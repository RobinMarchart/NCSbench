import atexit
import ncsbench.common.socket as s

EV3 = None
MOTOR = None

def run(args):
    global EV3, MOTOR
    EV3=args.type
    for port in [EV3.OUTPUT_A, EV3.OUTPUT_B, EV3.OUTPUT_C, EV3.OUTPUT_D]:
        
        m = EV3.MediumMotor(port)
        if m.connected:
            global MOTOR
            MOTOR = m
            break
    if not MOTOR:
        raise Exception("No motor connected")
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
