from pyfirmata import Arduino
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# sampling rate: 50Hz
samplingRate = 50


# That's our ringbuffer which accumluates the samples
# It's emptied every time when the plot window below
# does a repaint
ringbuffer = []


# updates the plot
def update(data):
    global plotbuffer
    global ringbuffer
    # add new data to the buffer
    plotbuffer = np.append(plotbuffer, ringbuffer)
    ringbuffer = []
    # only keep the 500 newest ones and discard the old ones
    plotbuffer = plotbuffer[-500:]
    # set the new 500 points of channel 9
    line.set_ydata(plotbuffer)
    return line,


# called from pyfirmata and appends data to the ringbuffer
def myCallback(v):
    global ringbuffer
    ringbuffer.append(v)


# now let's plot the data
fig, ax = plt.subplots()
# that's our plotbuffer
plotbuffer = np.zeros(500)
# plots an empty line
line, = ax.plot(plotbuffer)
# axis
ax.set_ylim(0, 1)


board = Arduino('/dev/ttyACM0')
board.samplingOn(50)
board.analog[0].register_callback(myCallback)
board.analog[0].enable_reporting()


# start the animation
ani = animation.FuncAnimation(fig, update, interval=100)

# show it and start the animation
plt.show()

#
board.samplingOff()

print("finished")
