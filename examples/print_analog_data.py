#!/usr/bin/python3

from pyfirmata2 import Arduino
import time

PORT = Arduino.AUTODETECT
# PORT = '/dev/ttyACM0'

# prints data on the screen at the sampling rate of 50Hz
# can easily be changed to saving data to a file

# It uses a callback operation so that timing is precise and
# the main program can just go to sleep.
# Copyright (c) 2018-2020, Bernd Porr <mail@berndporr.me.uk>
# see LICENSE file.


class AnalogPrinter:

    def __init__(self):
        # sampling rate: 10Hz
        self.samplingRate = 10
        self.timestamp = 0
        self.board = Arduino(PORT)

    def start(self):
        self.board.analog[0].register_callback(self.myPrintCallback)
        self.board.samplingOn(1000 / self.samplingRate)
        self.board.analog[0].enable_reporting()

    def myPrintCallback(self, data):
        print("%f,%f" % (self.timestamp, data))
        self.timestamp += (1 / self.samplingRate)

    def stop(self):
        self.board.samplingOff()
        self.board.exit()

print("Let's print data from Arduino's analogue pins for 10secs.")

# Let's create an instance
analogPrinter = AnalogPrinter()

# and start DAQ
analogPrinter.start()

# let's acquire data for 10secs. We could do something else but we just sleep!
time.sleep(10)

# let's stop it
analogPrinter.stop()

print("finished")
