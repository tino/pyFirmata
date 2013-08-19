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

# Time (approx. seconds) to get to the maximum/minimum
DURATION = 5
# Numbers of steps to get to the maximum/minimum
STEPS = 10 

# Creates a new board 
board = pyfirmata.Arduino(PORT)
print "Setting up the connection to the board ..."

# Definition of the pin, one with PWM, marked as ~XX on the Arduino
digital_0 = board.get_pin('d:11:p')

# Waiting time between the steps
wait_time = DURATION/float(STEPS)

# Note: Value range for PWM is 0.0 till 1.0
# Up
for i in range(1, STEPS + 1):
    value = i/float(STEPS)
    digital_0.write(value)
    board.pass_time(wait_time)

# Down
increment = 1/float(STEPS)
while STEPS > 0:
    value = increment * STEPS
    digital_0.write(value)
    board.pass_time(wait_time)
    STEPS = STEPS - 1

board.exit()
