def init(args):
    class ev3utils_container:
        def __init__(self,args):
            self.sensors={"1":args.lib.INPUT_1,"2":args.lib.INPUT_2,"3":args.lib.INPUT_3,"4":args.lib.INPUT_4}
            self.motors={"A":args.lib.OUTPUT_A,"B":args.lib.OUTPUT_B,"C":args.lib.OUTPUT_C,"D":args.lib.OUTPUT_D}
            from importlib import import_module
            self.util=import_module('.'+args.type,__name__)
    return ev3utils_container(args)