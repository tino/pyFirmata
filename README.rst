==========
pyFirmata2
==========

PyFirmata2 is an API which allows you to sample directly
analogue and digital data from the ports of your Arduino without
writing any C code. Just upload the default firmata sketch
into your Arduino and you are all set.

The Python API is fully compatible with Firmata 2.1, and has some
functionality of version 2.2. It runs on Python 2.7, 3.3, 3.4, 3.5
and 3.6

.. _Firmata: http://firmata.org

pyFirmata2 is an updated version of pyFirmata where you can
measure at a given sampling rate which then allows digital
filtering, for example with an realtime IIR filter.


Installation
============

First upload the standard firmata sketch into your Arduino with
File -> Examples -> Firmata -> Standard Firmata.

Then install pyFirmata2. The preferred way to install is with pip_::

    pip3 install pyfirmata2

You can also install from source with ``python setup.py install``. You will
need to have `setuptools`_ installed::

    git clone https://github.com/berndporr/pyFirmata2
    cd pyFirmata2
    python3 setup.py install

.. _pip: http://www.pip-installer.org/en/latest/
.. _setuptools: https://pypi.python.org/pypi/setuptools


Usage
=====

Basic usage::

    >>> from pyfirmata import Arduino
    >>> board = Arduino('/dev/tty.usbserial-A6008rIF')
    >>> board.digital[13].write(1)

To switch on contious data acquisition from the inputs of the board run::

    >>> board.samplingOn()

To enable sampling at the exact sampling interval (min 10ms)
use the optional argument of samplingOn::

    >>> board.samplingOn(samplinginterval in ms)

The individual analoge pins are enabled / read by:

    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

In order to process the data at the given sampling interval register a callback
handler::
  
    >>> board.analog[0].register_callback(myCallback)
    
where myCallback(data) is then called every time when data has been received
and is timed by the arduino itself. This is very precise up to 100Hz
sampling rate (10ms sampling interval).

If you use a pin more often, it can be worth using the ``get_pin`` method
of the board. It let's you specify what pin you need by a string, composed of
'a' or 'd' (depending on wether you need an analog or digital pin), the pin
number, and the mode ('i' for input, 'o' for output, 'p' for pwm). All
seperated by ``:``. Eg. ``a:0:i`` for analog 0 as input or ``d:3:p`` for
digital pin 3 as pwm.::

    >>> analog_0 = board.get_pin('a:0:i')
    >>> analog_0.read()
    0.661440304938
    >>> pin3 = board.get_pin('d:3:p')
    >>> pin3.write(0.6)

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
