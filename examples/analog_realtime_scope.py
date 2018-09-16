from pyfirmata2 import Arduino
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import signal as signal

# Realtime oscilloscope at a sampling rate of 50Hz
# It displays analog channel 0.
# You can plot multiple chnannels just by instantiating
# more RealtimePlotWindow instances and registering
# callbacks from the other channels.


# Creates a scrolling data display
class RealtimePlotWindow:

    def __init__(self):
        # create a plot window
        self.fig, self.ax = plt.subplots()
        # that's our plotbuffer
        self.plotbuffer = np.zeros(500)
        # create an empty line
        self.line, = self.ax.plot(self.plotbuffer)
        # axis
        self.ax.set_ylim(0, 1)
        # That's our ringbuffer which accumluates the samples
        # It's emptied every time when the plot window below
        # does a repaint
        self.ringbuffer = []
        # start the animation
        self.ani = animation.FuncAnimation(self.fig, self.update, interval=100)

    # updates the plot
    def update(self, data):
        # add new data to the buffer
        self.plotbuffer = np.append(self.plotbuffer, self.ringbuffer)
        # only keep the 500 newest ones and discard the old ones
        self.plotbuffer = self.plotbuffer[-500:]
        self.ringbuffer = []
        # set the new 500 points of channel 9
        self.line.set_ydata(self.plotbuffer)
        return self.line,

    # appends data to the ringbuffer
    def addData(self, v):
        self.ringbuffer.append(v)


# Create an instance of an animated scrolling window
# To plot more channels just create more instances and add callback handlers below
realtimePlotWindow = RealtimePlotWindow()

# sampling rate: 50Hz
samplingRate = 50

# create a 2nd order Butterworth lowpass with
# cutoff frequency at = 10 Hz and a gain of 5
cutoff = 10
gain = 5
lp_b, lp_a = signal.butter(2, cutoff/samplingRate*2.0)
lp_b = lp_b * gain
lp_z = signal.lfiltic(lp_b, lp_a, [0])

# our callback where we filter the data
def callBack(data):
    data, bp_z = signal.lfilter(lp_b, lp_a, [data], zi=lp_z)
    realtimePlotWindow.addData(data)

# Get the Ardunio board
board = Arduino('/dev/ttyACM0')

# Set the sampling rate in the Arduino
board.samplingOn(1000 / samplingRate)

# Register the callback which adds the data to the animated plot
board.analog[0].register_callback(callBack)

# Enable the callback
board.analog[0].enable_reporting()

# show the plot and start the animation
plt.show()

print("finished")
