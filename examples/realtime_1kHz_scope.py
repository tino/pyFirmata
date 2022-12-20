#!/usr/bin/python3
"""
Plots channel zero at 1kHz. Requires pyqtgraph.

Copyright (c) 2018-2021, Bernd Porr <mail@berndporr.me.uk>
see LICENSE file.

"""

import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

import numpy as np

from pyfirmata2 import Arduino

PORT = Arduino.AUTODETECT
# sampling rate: 1kHz
samplingRate = 1000

class QtPanningPlot:

    def __init__(self,layout,title):
        self.pw = pg.PlotWidget()
        layout.addWidget(self.pw)
        self.pw.setYRange(-1,1)
        self.pw.setXRange(0,500/samplingRate)
        self.plt = self.pw.plot()
        self.data = []
        # any additional initalisation code goes here (filters etc)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def update(self):
        self.data=self.data[-500:]
        if self.data:
            self.plt.setData(x=np.linspace(0,len(self.data)/samplingRate,len(self.data)),y=self.data)

    def addData(self,d):
        self.data.append(d)

app = pg.mkQApp()
mw = QtWidgets.QMainWindow()
mw.setWindowTitle('1kHz PlotWidget')
mw.resize(800,800)
cw = QtWidgets.QWidget()
mw.setCentralWidget(cw)

# Vertical arrangement
l = QtWidgets.QVBoxLayout()
cw.setLayout(l)

# Let's create a plot window
qtPanningPlot1 = QtPanningPlot(l,"Arduino 1st channel")
label = QtWidgets.QLabel("This label show how to add another Widget to the layout.")
l.addWidget(label)

# called for every new sample at channel 0 which has arrived from the Arduino
# "data" contains the new sample
def callBack(data):
    # filter your channel 0 samples here:
    # data = self.filter_of_channel0.dofilter(data)
    # send the sample to the plotwindow
    qtPanningPlot1.addData(data)

# Get the Ardunio board.
board = Arduino(PORT,debug=True)

# Set the sampling rate in the Arduino
board.samplingOn(1000 / samplingRate)

# Register the callback which adds the data to the animated plot
# The function "callback" (see above) is called when data has
# arrived on channel 0.
board.analog[0].register_callback(callBack)

# Enable the callback
board.analog[0].enable_reporting()

# Show the window
mw.show()

# showing all the windows
pg.exec()

# needs to be called to close the serial port
board.exit()

print("Finished")
