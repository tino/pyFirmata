#!/usr/bin/python3
"""
Plots channels zero and one at 100Hz. Requires pyqtgraph.

Copyright (c) 2018-2022, Bernd Porr <mail@berndporr.me.uk>
see LICENSE file.

"""

import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

import numpy as np

from pyfirmata2 import Arduino

PORT = Arduino.AUTODETECT
# sampling rate: 100Hz
samplingRate = 100

class QtPanningPlot:

    def __init__(self,title):
        self.pw = pg.PlotWidget()
        self.pw.setYRange(-1,1)
        self.pw.setXRange(0,500/samplingRate)
        self.plt = self.pw.plot()
        self.data = []
        # any additional initalisation code goes here (filters etc)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def getWidget(self):
        return self.pw
        
    def update(self):
        self.data=self.data[-500:]
        if self.data:
            self.plt.setData(x=np.linspace(0,len(self.data)/samplingRate,len(self.data)),y=self.data)

    def addData(self,d):
        self.data.append(d)

app = pg.mkQApp()
mw = QtWidgets.QMainWindow()
mw.setWindowTitle('100Hz dual PlotWidget')
mw.resize(800,800)
cw = QtWidgets.QWidget()
mw.setCentralWidget(cw)

# Let's arrange the two plots horizontally
layout = QtWidgets.QHBoxLayout()
cw.setLayout(layout)

# Let's create two instances of plot windows
qtPanningPlot1 = QtPanningPlot("Arduino 1st channel")
layout.addWidget(qtPanningPlot1.getWidget())

qtPanningPlot2 = QtPanningPlot("Arduino 2nd channel")
layout.addWidget(qtPanningPlot2.getWidget())

# called for every new sample at channel 0 which has arrived from the Arduino
# "data" contains the new sample
def callBack1(data):
    # filter your channel 0 samples here:
    # data = self.filter_of_channel0.dofilter(data)
    # send the sample to the plotwindow
    qtPanningPlot1.addData(data)

# called for every new sample at channel 1 which has arrived from the Arduino
# "data" contains the new sample
def callBack2(data):
    # filter your channel 1 samples here:
    # data = self.filter_of_channel1.dofilter(data)
    # send the sample to the plotwindow
    qtPanningPlot2.addData(data)

# Get the Ardunio board.
board = Arduino(PORT)

# Set the sampling rate in the Arduino
board.samplingOn(1000 / samplingRate)

# Register the callback which adds the data to the animated plot
board.analog[0].register_callback(callBack1)
board.analog[1].register_callback(callBack2)

# Enable the callback
board.analog[0].enable_reporting()
board.analog[1].enable_reporting()

# showing the plots
mw.show()

# Starting the QT GUI
# This is a blocking call and only returns when the user closes the window.
pg.exec()

# needs to be called to close the serial port
board.exit()

print("Finished")
