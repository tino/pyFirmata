# import modules
from pyfirmata import Arduino, pyfirmata, util
import time

buttonRead = False
pushButton = 8
ledPin = 9

board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

board.digital[ledPin].mode = pyfirmata.OUTPUT # define output mode

# create function to turn on and off led
def turn_on_led(pin_):
    board.digital[pin_].write(1) # 1 means power on

def turn_off_led(pin_):
    board.digital[pin_].write(0) # 0 means power off

button = board.get_pin(f'd:{pushButton}:i') #definindo pino
button.enable_reporting() #abrir leitura de valores nesse pino

""" util.Iterator()
Reads and manipulates data from the microcontroller through the serial port.
This method must be called in a main loop or in an Iterator instance to keep 
the board pin values up to date.
"""
iterator = util.Iterator(board)
iterator.start()

try:
    while True:
    
        buttonRead = button.read() #ler valores 
        print(button.read())
        time.sleep(0.075)

        if buttonRead:
            print("Led on")
            turn_on_led(ledPin) # call the function
        else:
            print( 'Led off')
            turn_off_led(ledPin) # call the function
        
        board.pass_time(1)
except KeyboardInterrupt:
	board.exit()