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

# Definition of the analog pins
PINS = (0, 1, 2, 3)

# Creates a new board 
board = pyfirmata.Arduino(PORT)
print "Setting up the connection to the board ..."

# Start an iterator thread
it = pyfirmata.util.Iterator(board)
it.start()

# Start reporting for defined pins
for pin in PINS:
    board.analog[pin].enable_reporting()

# Loop for reading the input. Duration approx. 10 s
for i in range(1, 11):
    print "\nValues after %i second(s)" % i
    for pin in PINS:
        print "Pin %i : %s" % (pin, board.analog[pin].read())
    board.pass_time(1)

board.exit()
