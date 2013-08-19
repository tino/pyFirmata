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

# Creates a new board 
board = pyfirmata.Arduino(PORT)
print "Setting up the connection to the board ..."

# Setup the digital pin
digital_0 = board.get_pin('d:6:i')

# Start an iterator thread
it = pyfirmata.util.Iterator(board)
it.start()
digital_0.enable_reporting()

while (True):
    #print "Button state: %s" % digital_0.read()
    # The return values are: True False, and None
    if str(digital_0.read()) == 'True':
        print "Button pressed."
    elif str(digital_0.read()) == 'False':
        print "Button not pressed."
    else: 
        print "Button was never pressed."
    board.pass_time(0.5)

board.exit()
