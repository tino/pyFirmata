from pyfirmata import Arduino, pyfirmata, util
import time, asyncio

### Start of pin configuration
board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

it = util.Iterator(board)
it.start()

sonarEcho = board.get_pin('d:8:i') #digital pin 7 INPUT
sonarTrig = board.get_pin('d:9:o') #digital pin 9 OUTPUT

time.sleep(1)

sonarEcho.enable_reporting()
### End pin configuration

try:
    while True:
        ##### SEE DATASHEET ######
        ##on
        sonarTrig.write(1)
        board.pass_time(2E-6)
        ##on
        sonarTrig.write(1)
        board.pass_time(10E-6)
        ##off
        sonarTrig.write(0)
        ##########################
        
        response = sonarEcho.read()

        if response is False:
            print("Something has been detected!")
        else:
            print("Nothing was detected!")
        
        board.pass_time(0.06)
except KeyboardInterrupt:
	board.exit()
