import pathlib

from ev3dev.pistorms import INPUT_1,INPUT_2,INPUT_3,INPUT_4,OUTPUT_A,OUTPUT_B,OUTPUT_C,OUTPUT_D,LargeMotor
from ev3dev.pistorms import TouchSensor as _TouchSensor
from ev3dev.pistorms import GyroSensor as _GyroSensor

MediumMotor=None

ports=pathlib.Path("/sys/class/lego-port")
port_cache={}

def find_n(port):
    if port in port_cache:
        return port_cache[port]
    else:
        for p in ports.iterdir():
            if not p.parts[-1][-1] in port_cache.items():
                pt=(p/"address").read_text()[:-1]
                port_cache[pt]=p.parts[-1][-1]
        return port_cache[port]

def set_touch(port):
    n=find_n(port)
    (ports/("port"+n)/"mode").write_bytes(b"ev3-analog")

def set_gyro(port):
    n=find_n(port)
    p=ports/("port"+n)
    (p/"mode").write_bytes(b"ev3-uart")
    (p/"set_device").write_bytes(b"lego-ev3-gyro")

class TouchSensor(_TouchSensor):
    def __init__(self,address,**kwargs):
        set_touch(address)
        super().__init__(address,**kwargs)

class GyroSensor(_GyroSensor):
    def __init__(self,address, **kwargs):
        set_gyro(address)
        super().__init__(address, **kwargs)

