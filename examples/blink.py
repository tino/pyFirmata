#!/usr/bin/python3

# Copyright (c) 2012, Fabian Affolter <fabian@affolter-engineering.ch>
# Copyright (c) 2019-2021, Bernd Porr <mail@berndporr.me.uk>
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
#
#
# This program toggles the digital port 13 on/off every second.
# Port 13 has an LED connected so you'll see def a flashing light!
# Coding is done with a timer callback to avoid evil loops / delays.

import pyfirmata2
from threading import Timer

class Blink():
    def __init__(self, board, seconds):
        # pin 13 which is connected to the internal LED
        self.digital_0 = board.get_pin('d:13:o')

        # flag that we want the timer to restart itself in the callback
        self.timer = None

        # delay
        self.DELAY = seconds

    # callback function which toggles the digital port and
    # restarts the timer
    def blinkCallback(self):
        # call itself again so that it runs periodically
        self.timer = Timer(self.DELAY,self.blinkCallback)

        # start the timer
        self.timer.start()
        
        # now let's toggle the LED
        v = self.digital_0.read()
        v = not v
        if v:
            print("On")
        else:
            print("Off")
        self.digital_0.write(v)

    # starts the blinking
    def start(self):
        # Kickstarting the perpetual timer by calling the
        # callback function once
        self.blinkCallback()

    # stops the blinking
    def stop(self):
        # Cancel the timer
        self.timer.cancel()

# main program

# Adjust that the port match your system, see samples below:
# On Linux: /dev/ttyACM0,
# On Windows: COM1, COM2, ...
PORT =  pyfirmata2.Arduino.AUTODETECT

# Creates a new board
board = pyfirmata2.Arduino(PORT)

t = Blink(board,1)
t.start()

print("To stop the program press return.")
# Just blocking here to do nothing.
input()

t.stop()

# close the serial connection
board.exit()
