# import modulus
from pyfirmata import Arduino, pyfirmata
import time

pin = 13 # serial port number

board = Arduino() # or Arduino(port) define board
print("Comunicação iniciada com sucesso!")

board.digital[pin].mode = pyfirmata.OUTPUT # set pin as output

# Create functions to turn LED on and off
def turn_on_led():
    board.digital[pin].write(1) # 1 led on
def turn_off_led():
    board.digital[pin].write(0) # 0 led off

while True:
    turn_on_led() # call and turn on
    time.sleep(1) # wait 1 second
    turn_off_led() # call and turn off
    time.sleep(1)
