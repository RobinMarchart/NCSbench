ev3_type=""
sensors,motors={},{}
INPUT_1,INPUT_2,INPUT_3,INPUT_4,OUTPUT_A,OUTPUT_B,OUTPUT_C,OUTPUT_D="","","","","","","",""
MediumMotor,LargeMotor,TouchSensor,GyroSensor=None,None,None,None
Button=None
def init(ev3:str):
    global ev3_type,sensors,motors,INPUT_1,INPUT_2,INPUT_3,INPUT_4,OUTPUT_A,OUTPUT_B,OUTPUT_C,OUTPUT_D,MediumMotor,LargeMotor,TouchSensor,GyroSensor,Button
    ev3_type=ev3
    from importlib import import_module
    lib=None
    try:
        lib=import_module('.'+ev3,__name__)
    except ModuleNotFoundError:
        lib=import_module("ev3dev."+ev3)
    sensors={"1":lib.INPUT_1,"2":lib.INPUT_2,"3":lib.INPUT_3,"4":lib.INPUT_4}
    motors={"A":lib.OUTPUT_A,"B":lib.OUTPUT_B,"C":lib.OUTPUT_C,"D":lib.OUTPUT_D}
    INPUT_1,INPUT_2,INPUT_3,INPUT_4,OUTPUT_A,OUTPUT_B,OUTPUT_C,OUTPUT_D=lib.INPUT_1,lib.INPUT_2,lib.INPUT_3,lib.INPUT_4,lib.OUTPUT_A,lib.OUTPUT_B,lib.OUTPUT_C,lib.OUTPUT_D
    MediumMotor,LargeMotor,TouchSensor,GyroSensor=lib.MediumMotor,lib.LargeMotor,lib.TouchSensor,lib.GyroSensor
    if "Button" in lib.__dir__:
        Button=lib.Button
    else:
        class B:
            up=false
        Button=B