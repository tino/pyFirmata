from threading import Thread
from pyfirmata import Arduino, pyfirmata, util
from pyfirmata.util import ping_time_to_distance
import time

### Start of pin configuration
board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

it = util.Iterator(board)
it.start()

sonarEcho = board.get_pin('d:7:o')

time.sleep(1)


### End set pins

class Echo(Thread):
	def __init__ (self, echoPino):
		Thread.__init__(self)
		self.echoPino = echoPino

	def run(self):
		while True:
			time = self.echoPino.ping()
			board.pass_time(0.06) #delay of 60ms -> see datasheet
			print(f"Time: {time}ms, distance: {ping_time_to_distance(time)}cm")
			
inicioEcho = Echo(sonarEcho)
inicioEcho.start()