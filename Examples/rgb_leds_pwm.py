# import modules
from pyfirmata import Arduino, pyfirmata, util
import time, random

pins = [9, 10, 11] #PWM pins

board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

RGB = [board.get_pin(f'd:{pin}:p') for pin in pins]

iterator = util.Iterator(board)
iterator.start()

# create function to turn on and off led
def turn_on_led(pin_, value):
    RGB[pin_].write(value) # 1 means power on

def turn_off_led():
    for pin in range(len(pins)):
        RGB[pin].write(0) # 0 means power off

try:
    random.seed()
    while True:
        for pin in range(len(pins)):
            value = random.random() 
            turn_on_led(pin, value)
        time.sleep(0.5)
        turn_off_led()
except KeyboardInterrupt:
	board.exit()