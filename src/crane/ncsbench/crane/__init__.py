import atexit

EV3 = None
MOTOR = None

def run(args):
    global EV3, MOTOR
    EV3=args.type
    for port in [EV3.OUTPUT_A, EV3.OUTPUT_B, EV3.OUTPUT_C, EV3.OUTPUT_D]:
        try:
            m = EV3.MediumMotor(port)
            m.stop()
            MOTOR = m
        except Exception:
            pass
    MOTOR.polarity = 'inversed'
    atexit.register(stop_coast)
    from ncsbench.common.control_socket import CraneSocket
    CraneSocket((args.address,args.cport),False)

def stop():
    MOTOR.stop(stop_action='hold')

def up():
    MOTOR.run_forever(speed_sp=500, ramp_up_sp=10000)

def down():
    MOTOR.run_to_rel_pos(position_sp=-130, speed_sp=100, ramp_up_sp=0,stop_action='coast')

def stop_coast():
    MOTOR.stop(stop_action='coast')
