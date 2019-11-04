import atexit
import ncsbench.common.socket as s

EV3 = None
MOTOR = None

def run(args):
    global EV3, MOTOR
    EV3=args.lib
    if args.type=="pistorms":
        print("unsupported platform: pistorms")
        print("\tstopping...")
        exit(1)
    m = EV3.MediumMotor(EV3.motors[args.motor_port])
    if m.connected:
        global MOTOR
        MOTOR = m
    if not MOTOR:
        print("couldnt find Motor on port "+args.motor_port)
        print("\tstopping...")
        exit(1)
    MOTOR.polarity = 'inversed'
    atexit.register(stop_coast)
    if args.manual:
        import enum
        class State(enum.Enum):
            Null=0
            Up=1
            Down=2
            Stop=3
        state=[State.Null]
        def up_hook(state_n,state):
            if state_n:
                if state!=State.Up:
                    state=State.Up
                    up()
            else:
                if state==State.Up:
                    state=State.Null
        EV3.Button.on_up=lambda state_n:up_hook(state_n,state[0])
        def down_hook(state_n,state):
            if state_n:
                if state!=State.Down:
                    state=State.Down
                    down()
            else:
                if state==State.Down:
                    state=State.Null
        EV3.Button.on_down=lambda state_n:down_hook(state_n,state[0])
        def stop_hook(state_n,state):
            if state_n:
                if state!=State.Stop:
                    state=State.Stop
                    stop()
            else:
                if state==State.Stop:
                    state=State.Null
        EV3.Button.on_enter=lambda state_n:stop_hook(state_n,state[0])
        import time
        while not EV3.Button.backspace:
            EV3.Button.process()
            time.sleep(0.2)

    else:
        args.sock.events[s.EVENTS.CRANE_STOP].always.add(lambda data:stop())
        args.sock.events[s.EVENTS.CRANE_UP].always.add(lambda data:up())#TODO timed up and response
        args.sock.events[s.EVENTS.CRANE_DOWN].always.add(lambda data:down())
        args.sock.events[s.EVENTS.EXIT].always.add(lambda data:exit(0))
        args.sock.send(s.EVENTS.READY)

def stop():
    MOTOR.stop(stop_action='hold')

def up():
    MOTOR.run_forever(speed_sp=500, ramp_up_sp=10000)

def down():
    MOTOR.run_timed(time_sp=1, speed_sp=100, ramp_up_sp=0,stop_action='coast')

def stop_coast():
    MOTOR.stop(stop_action='coast')
