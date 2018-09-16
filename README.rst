==========
pyFirmata2
==========

PyFirmata2 is an API which allows you to sample
analogue and digital ports of your Arduino without
writing any C code. Just upload the default firmata sketch
onto your Arduino and you are all set.

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

Upload the standard firmata sketch onto your Arduino with
File -> Examples -> Firmata -> Standard Firmata.


Install pyfirmata
--------------------

The preferred way to install is with pip_::

    pip3 install pyfirmata2

You can also install from source with ``python3 setup.py install``. You will
need to have `setuptools`_ installed::

    git clone https://github.com/berndporr/pyFirmata2
    cd pyFirmata2
    python3 setup.py install

.. _pip: http://www.pip-installer.org/en/latest/
.. _setuptools: https://pypi.python.org/pypi/setuptools


Usage
=====

Initialisation
--------------

Specify the serial USB port in the constructor of `Arduino`::

    >>> from pyfirmata import Arduino
    >>> board = Arduino('/dev/ttyACM0')

Writing to a digital pin
------------------------

Digital ports can written to at any time::
  
    >>> board.digital[13].write(1)

Starting sampling at a given sampling interval
----------------------------------------------

To measure analoge data you need to specify a
sampling interval in ms:: 

    >>> board.samplingOn(samplinginterval in ms)

The smallest reliable interval is 10ms.
Calling just `samplingOn()` without its argument sets
the sampling interval to 19ms.

Enabling and reading from individual analoge pins
-------------------------------------------------

To process the data at the given sampling interval register a callback
handler and then enable it::
  
    >>> board.analog[0].register_callback(myCallback)
    >>> board.analog[0].enable_reporting()
    
where `myCallback(data)` is then called at the given sampling rate
with the received data.

The value of any enabled pin is also stored internally and
you can read its value with the `read()` method any time::

    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

This allows you to read it within a loop or you can read
additional pins in an event handler if you want to
sample from more than one analoge/digital pin at the same time. For
example you could register an event handler for the analogue pin
0 and then in the event handler read the other analogue pins 1 and 2.


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


Example code
============

The subdirectory ``examples`` on github
(https://github.com/berndporr/pyFirmata2) contains the demo programs.
Here is a list with a short description::

Realtime oscillsocope with realtime filtering
---------------------------------------------

The `animation` function of `matplotlib` is used to create
scrolling animated plotwindow displaying the data. This
is implemented as a class so that it's easy to add more plot
windows for other channels. If you want to plot more channels
in the same window then just use the `read()` function within the
handler to read the other pins.

The data is filtered with a 2nd order lowpass filter.
This is achieved by the `scipy` filter
functions `lfilter` and `butter`. Note the cumbersome use
of these filters to establish a realtime filter. Their
internal states are not kept from time step to time step
so they need to be fed back into the filter every time.


Digital port reader
-------------------

This demo reads a digital port in a loop with a delay. This
won't give precise timing but is OK for simple tasks.

Analogue data printer
---------------------

A program which *prints samples to stdout* using the callback handler.
The program as it is can be used to pipe data into a file and
then plotted with gnuplot for example.


Flashing LED
------------

Simplest case scenario where the internal LED on the Arduino
is switched on/off using the delay function of the pyfirmata2 library.
Here, sampling is switched off and the timing is only approximately
given because of the unreliable delay.


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
