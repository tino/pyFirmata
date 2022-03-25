from threading import Thread
from pyfirmata import Arduino, pyfirmata, util
import time, asyncio

### Start pin configuration
board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

it = util.Iterator(board)
it.start()

sonarEcho = board.get_pin('d:8:i')
sonarTrig = board.get_pin('d:9:o')

time.sleep(1)

sonarEcho.enable_reporting()
### End pin configuration

class Echo(Thread):
	def __init__ (self, board, echoPino, trigPino):
		Thread.__init__(self)
		self.echoPino = echoPino
		self.trigPino = trigPino
		self.board = board

	def run(self):
		while True:
			##### SEE DATASHEET ######
			##on
			self.trigPino.write(1)
			board.pass_time(2E-6)
			
			##on
			self.trigPino.write(1)
			board.pass_time(10E-6)
			##off
			self.trigPino.write(0)
			##########################
			
			echo_end = self.echoPino.read()

			if echo_end is False:
				print("Algo foi detectado!")
			else:
				print("Nada foi detectado!")
			board.pass_time(0.06)


inicioEcho = Echo(board, sonarEcho, sonarTrig)
inicioEcho.start()
print("Thead started!")
