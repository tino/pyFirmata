=========
pyFirmata
=========

pyFirmata is a Python interface for the `Firmata`_ protocol. It is fully
compatible with Firmata 2.1, and has some functionality of version 2.2. It runs
on Python 2.7, 3.3 and 3.4.

.. _Firmata: http://firmata.org

Test & coverage status:

.. image:: https://travis-ci.org/tino/pyFirmata.png?branch=master
    :target: https://travis-ci.org/tino/pyFirmata

.. image:: https://coveralls.io/repos/github/tino/pyFirmata/badge.svg?branch=master
    :target: https://coveralls.io/github/tino/pyFirmata?branch=master

Installation
============

The preferred way to install is with pip_::

    pip install pyfirmata

You can also install from source with ``python setup.py install``. You will
need to have `setuptools`_ installed::

    git clone https://github.com/tino/pyFirmata
    cd pyFirmata
    python setup.py install

.. _pip: http://www.pip-installer.org/en/latest/
.. _setuptools: https://pypi.python.org/pypi/setuptools


Usage
=====

Basic usage::

    >>> from pyfirmata import Arduino, util
    >>> board = Arduino('/dev/tty.usbserial-A6008rIF')
    >>> board.digital[13].write(1)

To always have the most recent reading from the analog ports, the function board.iterator
needs to be called periodically. This can be achieved with the utility class util.Iterator
which starts up a new thread and then calls board.iterator as fast as possible::

    >>> util.Iterator(board).start()
    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

If you want to process data at a given sampling rate you can register a callback
handler::
  
    >>> board.analog[0].register_callback(myCallback)
    
where myCallback(data) is then called every time when data has been received.
The sampling rate can be set by the method (default is 1/0.019 Hz)::

    >>> board.setSamplingRate(samplingRate)

If you use a pin more often, it can be worth it to use the ``get_pin`` method
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

Todo
====

The next things on my list are to implement the new protocol changes in
firmata:

- Pin State Query, which allows it to populate on-screen controls with an
  accurate representation of the hardware's configuration
  (http://firmata.org/wiki/Proposals#Pin_State_Query_.28added_in_version_2.2.29)
