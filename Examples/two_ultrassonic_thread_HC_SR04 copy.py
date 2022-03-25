from threading import Thread
from pyfirmata import Arduino, pyfirmata, util
from pyfirmata.util import ping_time_to_distance
import time

### Start of pin configuration
board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

it = util.Iterator(board)
it.start()

## Note: Echo and Trigger pins connected to the same ports
sonarEcho1 = board.get_pin('d:7:o') ## digital pin 7 OUTPUT
sonarEcho2 = board.get_pin('d:8:o') ## digital pin 8 OUTPUT

time.sleep(1)


### End set pins

class Echo(Thread):
	def __init__ (self, echoPino, text:str=None):
		Thread.__init__(self)
		self.echoPino = echoPino
		self.text = text

	def run(self):
		while True:
			time = self.echoPino.ping()
			board.pass_time(0.06) #delay of 60ms -> see datasheet
			distance = ping_time_to_distance(time)
			print(f"{self.text}".format(time, distance))

##Sonar 1: port 7
text_sonar1 = "sonar1: Time: {0}ms, distance: {1}cm"
inicioEcho1 = Echo(sonarEcho1, text_sonar1)
inicioEcho1.start()

##Sonar 1: port 8
text_sonar2 = "sonar2: Time: {0}ms, distance: {1}cm"
inicioEcho2 = Echo(sonarEcho2, text_sonar2)
inicioEcho2.start()