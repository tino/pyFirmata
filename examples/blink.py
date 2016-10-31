#!/usr/bin/env python
# 
# Copyright (c) 2012-2013, Fabian Affolter <fabian@affolter-engineering.ch>
#
# Released under the MIT license. See LICENSE file for details.

import pyfirmata

# Adjust that the port match your system, see samples below:
# On Linux: /dev/tty.usbserial-A6008rIF, /dev/ttyACM0, 
# On Windows: \\.\COM1, \\.\COM2
PORT = '/dev/ttyACM0'

# Pin 11 is used
PIN = 11

# A 2 seconds delay
DELAY = 2 

# Creates a new board 
board = pyfirmata.Arduino(PORT)
print "Setting up the connection to the board ..."

# Loop for blinking the led
while True:
    # Set the LED pin to 1 (HIGH)
    board.digital[PIN].write(1) 
    board.pass_time(DELAY)
    # Set the LED pin to 0 (LOW)
    board.digital[PIN].write(0) 
    board.pass_time(DELAY)

board.exit()
