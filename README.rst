==========
pyFirmata2
==========

PyFirmata2 turns your Arduino into a data acquisition card which
you can directly program with Python.

Just upload the default firmata sketch into your Arduino and you are all set.

pyFirmata2 is an updated version of pyFirmata which adds precise sampling
to the API so that it's possible to filter signals and in general do
signal processing. Instead of "sleep" commands which have unreliable timing
the Arduino performs the sampling in its firmware and transmits the data
then to pyFirmata2. The python application simply registers a callback
which is then called after new data has arrived.


Installation
============


Upload firmata
--------------

Upload the standard firmata sketch into your Arduino with::
  
    File -> Examples -> Firmata -> Standard Firmata



Install pyfirmata2
------------------

The preferred way to install is with `pip` / `pip3`. Under Linux::

    pip3 install pyfirmata2

    
and under Windows/Mac type::
  
    pip install pyfirmata2

    
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

Specify the serial USB port in the constructor of the `Arduino` class::

    from pyfirmata import Arduino
    board = Arduino(Arduino.AUTODETECT)

which tries to detect automatically the port on the system.

If this fails you can also specify the port manually::

    board = Arduino('COM4')

Under Linux this is usually `/dev/ttyACM0`. Under Windows it is a
COM port, for example `COM4`. On a MAC it's `/dev/ttys000`, `/dev/cu.usbmodem14101` or
check for the latest addition to `/dev/*`.


Starting sampling at a given sampling interval
----------------------------------------------

In order to sample analoge data you need to specify a
sampling interval in ms. The smallest reliable interval is 10ms::

    board.samplingOn(samplinginterval in ms)

Calling `samplingOn()` without its argument sets
the sampling interval to 19ms.


Enabling and reading from an analoge pins
-------------------------------------------------

To process the data at the given sampling interval register a callback
handler and then enable it::
  
    board.analog[0].register_callback(myCallback)
    board.analog[0].enable_reporting()
    
where `myCallback(data)` is then called every time after data has been received
and is timed by the arduino itself.

You can also read the analoge value of a port any time by issuing a read
command::

    board.analog[0].read()

This is useful for reading additional pins within a callback handler
to process multiple pins simultaneously. Note that the data obtained
by `read()` is read from an internal buffer which stores the most
recent value received from the Arduino.



Writing to a digital port
-------------------------

Digital ports can be written to at any time::
  
    board.digital[13].write(1)

For any other functionality use the pin class.

    
The pin class
-------------
The command `get_pin` requests the class of a pin
by specifying a string, composed of
'a' or 'd' (depending on wether you need an analog or digital pin), the pin
number, and the mode ('i' for input, 'o' for output, 'p' for pwm). All
seperated by `:`. Eg. `a:0:i` for analog 0 as input or `d:3:p` for
digital pin 3 as pwm::

    analog_0 = board.get_pin('a:0:i')
    analog_0.read()
    pin3 = board.get_pin('d:3:p')
    pin3.write(0.6)


Example code
============

The directory https://github.com/berndporr/pyFirmata2/tree/master/examples 
contains a realtime Oscillsocope with precise sampling rate,
a digital port reader, the ubiquitous flashing LED program and
a program which prints data using the callback handler.


Credits
=======

The original pyFirmata has been written by Tino de Bruijn.
The realtime sampling / callback has been added by Bernd Porr.
