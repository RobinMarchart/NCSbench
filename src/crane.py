import ev3dev.ev3,atexit
class Crane:
	def __init__(self,port):
		self.motor=ev3dev.ev3.MediumMotor(port)
		self.motor.polarity='inversed'
		def stop(c):
			c.stop_coast()
		atexit.register(stop,(self,))
	
	def stop(self):
		self.motor.stop(stop_action='hold')
	
	def up(self):
		self.motor.run_forever(speed_sp=500,ramp_up_sp=10000)
	
	def down(self):
		self.motor.run_to_rel_pos(position_sp=-130,speed_sp=100,ramp_up_sp=0,stop_action='coast')
	
	def stop_coast(self):
		self.motor.stop(stop_action='coast')