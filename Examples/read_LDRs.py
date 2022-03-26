#import modulus
from pyfirmata import Arduino, pyfirmata, util
import time

##LDR analog ports
led1PullDw = 0
led2PullUp = 1

#Identifying the board
board = Arduino() # or Arduino(port) define board
print("Communication started successfully!")

## Starting Iterator
"""To use analog ports, it is probably useful to start an iterator thread.
   Otherwise, the board will keep sending data to your serial, until it overflows:"""
it = util.Iterator(board)
it.start()

##Setting pin status
ldr1 = board.get_pin(f'a:{led1PullDw}:i') #a = analog and i = input
ldr2 = board.get_pin(f'a:{led2PullUp}:i') #a = analog and i = input

##Iniciando
ldr1.enable_reporting()
ldr2.enable_reporting()

try:
   while True:
      ## read LDRs
      ldr1_ = ldr1.read()
      ldr2_ = ldr2.read()
      print(f'LDR PullDown: {ldr1_}, LDR PullUp: {ldr2_}')
      time.sleep(0.3) #300 milliseconds ou 300ms
except KeyboardInterrupt:
   board.exit()