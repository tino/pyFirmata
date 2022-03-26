# import modules
from pyfirmata import Arduino, pyfirmata
import time

pins = [9, 10, 11] #PWM pins

board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

for pin in pins:
    board.digital[pin].mode = pyfirmata.OUTPUT # define output mode

# create function to turn on and off led
def turn_on_led(pin_):
    board.digital[pin_].write(1) # 1 means power on

def turn_off_led(pin_):
    board.digital[pin_].write(0) # 0 means power off

#Turn off all LEDs except pin
def turn_off(pin):
    for pin_ in pins:
        if pin_ == pin: continue #skip this pin
        turn_off_led(pin_)

try:
    while True:
        for pin in pins:
            turn_on_led(pin) # call the function
            time.sleep(0.5) # wait for 500 ms and turn off led! 
        turn_off(pin) #call the function
except KeyboardInterrupt:
	board.exit()