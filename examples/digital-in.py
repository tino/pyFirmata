#!/usr/bin/python3

# Copyright (c) 2012, Fabian Affolter <fabian@affolter-engineering.ch>
# Copyright (c) 2018-2021, Bernd Porr <mail@berndporr.me.uk>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the pyfirmata team nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pyfirmata2

# The program monitors the digital pin 6.
# Connect a switch between pin 6 and GND.
# Whenever there is a change of the state
# at pin 6 the callback function "pinCallback"
# is called.

# Adjust that the port match your system, see samples below:
# On Linux: /dev/tty.usbserial-A6008rIF, /dev/ttyACM0,
# On Windows: \\.\COM1, \\.\COM2
# PORT = '/dev/ttyACM0'
PORT = pyfirmata2.Arduino.AUTODETECT


# Callback function which is called whenever there is a
# change at the digital port 6.
def pinCallback(value):
    if value:
        print("Button released")
    else:
        print("Button pressed")
    

# Creates a new board
board = pyfirmata2.Arduino(PORT)
print("Setting up the connection to the board ...")

# default sampling interval of 19ms
board.samplingOn()

# Setup the digital pin with pullup resistor: "u"
digital_0 = board.get_pin('d:6:u')

# points to the callback
digital_0.register_callback(pinCallback)

# Switches the callback on
digital_0.enable_reporting()

print("To stop the program press return.")

# Do nothing here. Just preventing the program from reaching the
# exit function.
input()

# Close the serial connection to the Arduino
board.exit()
