==========
pyFirmata2
==========

PyFirmata2 turns your Arduino into a data acquisition card controlled by Python.

Up to 100Hz precise sampling at the analogue ports for digital filtering.

Just upload the default firmata sketch into your Arduino and you are all set.

pyFirmata2 is an updated version of pyFirmata which adds *precise sampling of the analogue inputs*
to the API so that it's possible to filter signals and in general do
signal processing. Instead of "sleep" commands which have unreliable timing
the Arduino performs the sampling in its firmware and transmits the data
then to pyFirmata2. The Python application simply registers a callback
which is then called every time after new data has arrived.

This API has been used in my Digital Signal Processing (DSP) class to
practise realtime filtering of analogue sensor
data. Examples can be viewed on the YouTube channel of the
class: https://www.youtube.com/user/DSPcourse


Installation
============


Upload firmata
--------------

Install the Arduino IDE on your computer: https://www.arduino.cc/en/Main/Software

Start the IDE and upload the standard firmata sketch into your Arduino with::
  
    File -> Examples -> Firmata -> Standard Firmata



Install pyfirmata2
------------------

The preferred way to install is with `pip` / `pip3`. Under Linux::

    pip3 install pyfirmata2 [--user] [--upgrade]

    
and under Windows/Mac type::
  
    pip install pyfirmata2 [--user] [--upgrade]

    
You can also install from source with::

    git clone https://github.com/berndporr/pyFirmata2
    cd pyFirmata2

Under Linux type::
  
    python3 setup.py install

Under Windows / Mac::

    python setup.py install


Usage
=====


Initialisation
--------------

Create an instance of the `Arduino` class::

    from pyfirmata import Arduino
    board = Arduino(Arduino.AUTODETECT)

which automatically detects the serial port of the Arduino.

If this fails you can also specify the serial port manually, for example::

    board = Arduino('COM4')

Under Linux this is usually `/dev/ttyACM0`. Under Windows this is a
COM port, for example `COM4`. On a MAC it's `/dev/ttys000`, `/dev/cu.usbmodem14101` or
check for the latest addition: `ls -l -t /dev/*`.


Starting sampling at a given sampling interval
----------------------------------------------

In order to sample analogue data you need to specify a
sampling interval in ms. The smallest interval is 10ms::

    board.samplingOn(samplinginterval in ms)

Calling `samplingOn()` without its argument sets
the sampling interval to 19ms.


Enabling and reading from analoge pins
-------------------------------------------------

To process data at a given sampling interval register a callback
handler and then enable it::
  
    board.analog[0].register_callback(myCallback)
    board.analog[0].enable_reporting()
    
where `myCallback(data)` is then called every time after data has been received
and is timed by the arduino itself.

You can also read additional analogue pins any time by issuing a read
command::

    board.analog[1].read()

This is useful for reading additional pins within a callback handler
to process multiple pins simultaneously. Note that the data obtained
by `read()` is read from an internal buffer which stores the most
recent value received from the Arduino. This call is non-blocking.
You also need to run `enable_reporting()` on that pin before you can use `read()`.


Writing to a digital port
-------------------------

Digital ports can be written to at any time::
  
    board.digital[13].write(1)

For any other functionality use the pin class below.

    
The pin class
-------------
The command `get_pin` requests the class of a pin
by specifying a string, composed of
'a' or 'd' (depending on if you need an analog or digital pin), the pin
number, and the mode ('i' for input, 'o' for output, 'p' for pwm). All
seperated by `:`. Eg. `a:0:i` for analog 0 as input or `d:3:p` for
digital pin 3 as pwm::

    analog_0 = board.get_pin('a:0:i')
    analog_0.read()
    pin3 = board.get_pin('d:3:p')
    pin3.write(0.6)
	
	
Closing the board
-----------------
To close the serial port to the Arduino use the exit command::
    
	board.exit()


Example code
============

The directory https://github.com/berndporr/pyFirmata2/tree/master/examples 
contains two realtime Oscilloscopes with precise sampling rate,
a digital port reader, the ubiquitous flashing LED program and
a program which prints data using the callback handler.


Troubleshooting
===============

Spyder
------

Start your program from the (Anaconda-) console / terminal and never within Spyder. Here is
an example for Windows::

    (base) D:\>
    (base) D:\>cd pyFirmata2\examples
    (base) D:\pyFirmata2\examples>python realtime_two_channel_scope.py

The problem with Spyder is that it won't let your Python program terminate properly
which leaves the serial port in an undefined state. If you then re-run your program
it won't be able to talk to your Arduino. In the worst case you need to reboot your
computer. Bottomline: use Spyder for editing, run the program from the console / terminal.


After an update still the old version is being used
---------------------------------------------------

If you use the `--user` option to install / update packages Python might keep older versions.

Solution: Do a `pip uninstall pyfirmata2` multiple times until no version is left 
on your computer. Then install it again as described above.




Credits
=======

The original pyFirmata was written by Tino de Bruijn.
The realtime sampling / callback has been added by Bernd Porr.
