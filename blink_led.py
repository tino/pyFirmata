# import modules
from pyfirmata import Arduino, pyfirmata
import time

pin = 13 # Put the number of digital pin where black wire is connected in circuit

board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

board.digital[pin].mode = pyfirmata.OUTPUT # define output mode

# create function to turn on and off led
def turn_on_led():
    board.digital[pin].write(1) # 1 means power on
def turn_off_led():
    board.digital[pin].write(0) # 0 means power off

while True:
    turn_on_led() # call the function
    time.sleep(1) # wait for 2 seconds and turn off led! 
    turn_off_led() # call the function
    time.sleep(1)
