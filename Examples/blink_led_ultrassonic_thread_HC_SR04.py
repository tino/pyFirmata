## See Figures/blink_ultrassonics_thread.png
from threading import Thread
from pyfirmata import Arduino, pyfirmata, util
from pyfirmata.util import ping_time_to_distance
import time

##global variables
dist_max = 400 #in cm
dist_min = 2 #in cm
pwm_max = 1
pwm_min = 0

### Start of pin configuration
board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

it = util.Iterator(board)
it.start()

## Note: Echo and Trigger pins connected to the same ports
sonarEcho = board.get_pin('d:8:o') ## digital pin 7 OUTPUT
ledPin = board.get_pin('d:9:p')    ## pwm pin 9 OUTPUT

time.sleep(1)

### End set pins
class Sonar(Thread):
	def __init__ (self, echoPino, ledPin):
		Thread.__init__(self)
		self.echoPino = echoPino
		self.ledPin = ledPin

	def led_on_of(self, x): 
		self.ledPin.write(x)

	def mapping(self, value, xmin, xmax, ymin, ymax):
		"""TODO:
			The equation I used below is the same thing as the map() function in the Arduino language, that is, it just maps, in this case, centimeters to PWM values.
			Atention! Don't use the function name as map() as this is already a built-in Python function!
		"""
		line_eq = ((value - xmin)*(ymax-ymin))/(xmax-xmin) + ymin
		return line_eq

	def distance_blink(self, distance):
		dist_map = self.mapping(distance, 4, 200, 1, 0)
		dist_map = 0 if dist_map < 0 else dist_map
		#for pulse in range(pulses_map):
		self.led_on_of(dist_map)    #led on
		board.pass_time(0.1) #delay 100ms
		self.led_on_of(0)    #led off
		board.pass_time(0.1) #delay 100ms

	def run(self):
		while True:
			time = self.echoPino.ping()
			board.pass_time(0.06)                  #delay of 60ms -> see datasheet
			distance = ping_time_to_distance(time) #distance in cm
			self.distance_blink(distance)          #call distance()

##Start Sonar Class
sonarClass = Sonar(sonarEcho, ledPin)
sonarClass.start()
