from pyfirmata import Arduino, pyfirmata, util
from pyfirmata.util import ping_time_to_distance
import time

### Início da configuração de pinos
board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

it = util.Iterator(board)
it.start()

sonarEcho = board.get_pin('d:7:o')

time.sleep(1)

### End set pins

while True:
	time = sonarEcho.ping()
	board.pass_time(0.06) #delay of 60ms -> see datasheet
	print(f"Time: {time}ms, distance: {ping_time_to_distance(time)}cm")