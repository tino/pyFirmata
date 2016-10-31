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

# Prints some details to STDOUT
print "pyFirmata version:\t%s" % pyfirmata.__version__
print "Hardware:\t\t%s" % board.__str__()
#print "Firmata firmware name:  %s" % board.get_firmware()
print "Firmata firmware:\t%i.%i" % \
    (board.get_firmata_version()[0], board.get_firmata_version()[1])
