from pyfirmata import Arduino
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


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
# To plot more channels just create more instances
realtimePlotWindow = RealtimePlotWindow()

# Get the Ardunio board
board = Arduino('/dev/ttyACM0')

# sampling rate: 50Hz
samplingRate = 50

# Set the sampling rate in the Arduino
board.samplingOn(samplingRate)

# Register the callback which adds the data to the animated plot
board.analog[0].register_callback(realtimePlotWindow.addData)

# Enable the callback
board.analog[0].enable_reporting()

# show the plot and start the animation
plt.show()

print("finished")
