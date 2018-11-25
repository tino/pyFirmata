==========
pyFirmata2
==========

PyFirmata2 is an API which allows you to sample
analogue and digital ports of your Arduino without
writing any C code. Just upload the default firmata sketch
into your Arduino and you are all set.

The Python API is fully compatible with Firmata 2.1, and has some
functionality of version 2.2. It runs on Python 2.7, 3.3, 3.4, 3.5
and 3.6

.. _Firmata: http://firmata.org

pyFirmata2 is an updated version of pyFirmata where you can
measure at a given sampling rate which then allows digital
filtering, for example with a realtime IIR filter.


Installation
============


Upload firmata
-----------------

Upload the standard firmata sketch into your Arduino with
``File -> Examples -> Firmata -> Standard Firmata``.


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

Specify the serial USB port in the constructor of the ``Arduino`` class::

    >>> from pyfirmata import Arduino
    >>> board = Arduino('/dev/ttyACM0')

Under Linux this is usually ``/dev/ttyACM0``. Under Windows it is a
COM port, for example ``COM4``. On a MAC it's `/dev/ttys000`, `/dev/cu.usbmodem14101` or
check for the latest addition to `/dev/*`.


Writing to a digital pin
------------------------

Digital ports can be written to at any time::
  
    >>> board.digital[13].write(1)

Starting sampling at a given sampling interval
----------------------------------------------

In order to sample analoge data you need to specify a
sampling interval in ms. The smallest reliable interval is 10ms.

    >>> board.samplingOn(samplinginterval in ms)

Calling ``samplingOn()`` without its argument sets
the sampling interval to 19ms.

Enabling and reading from individual analoge pins
-------------------------------------------------

To process the data at the given sampling interval register a callback
handler and then enable it::
  
    >>> board.analog[0].register_callback(myCallback)
    >>> board.analog[0].enable_reporting()
    
where `myCallback(data)` is then called every time after data has been received
and is timed by the arduino itself.

You can also read the analoge value of a port any time by issuing a read
command::

    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

If timing is not important you can use this approach in a loop.  This
is also useful for reading additional pins within a callback handler
to process multiple pins simultaneously. Note that the data obtained
by ``read()`` is read from an internal buffer which stores the most
recent value received from the arduino.

If you use a pin more often, it can be worth using the ``get_pin`` method
of the board. It lets you specify what pin you need by a string, composed of
'a' or 'd' (depending on wether you need an analog or digital pin), the pin
number, and the mode ('i' for input, 'o' for output, 'p' for pwm). All
seperated by ``:``. Eg. ``a:0:i`` for analog 0 as input or ``d:3:p`` for
digital pin 3 as pwm.::

    >>> analog_0 = board.get_pin('a:0:i')
    >>> analog_0.read()
    0.661440304938
    >>> pin3 = board.get_pin('d:3:p')
    >>> pin3.write(0.6)


Example code
============

The directory https://github.com/berndporr/pyFirmata2/tree/master/examples 
contains a realtime Oscillsocope with precise sampling rate,
a digital port reader, the ubiquitous flashing LED program and
a program which prints data using the callback handler.


Board layout
============

If you want to use a board with a different layout than the standard Arduino
or the Arduino Mega (for which there exist the shortcut classes
``pyfirmata.Arduino`` and ``pyfirmata.ArduinoMega``), instantiate the Board
class with a dictionary as the ``layout`` argument. This is the layout dict
for the Mega for example::

    >>> mega = {
    ...         'digital' : tuple(x for x in range(54)),
    ...         'analog' : tuple(x for x in range(16)),
    ...         'pwm' : tuple(x for x in range(2,14)),
    ...         'use_ports' : True,
    ...         'disabled' : (0, 1, 14, 15) # Rx, Tx, Crystal
    ...         }

Credits
=======

The original pyFirmata has been written by Tino de Bruijn.
The realtime sampling / callback has been added by Bernd Porr.
