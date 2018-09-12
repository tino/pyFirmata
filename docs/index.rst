.. pyFirmata documentation master file, created by
   sphinx-quickstart on Wed Feb 17 18:59:00 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyFirmata's documentation!
=====================================

Module reference:

.. toctree::
   :maxdepth: 2

   pyfirmata

Installation
============

The preferred way to install is with pip_::

    pip install pyfirmata

If you install from source with ``python setup.py install``, don't forget to install ``pyserial`` as well.

.. _pip: http://www.pip-installer.org/en/latest/

Usage
=====

Basic usage::

    >>> from pyfirmata import Arduino, util
    >>> board = Arduino('/dev/tty.usbserial-A6008rIF')
    >>> board.digital[13].write(1)

To switch on data acquisition from the inputs of the board run::

    >>> board.samplingOn()

and they will be updated approximately every 19ms. Or enable sampling
with the exact sampling rate::

    >>> board.samplingOn(samplingrate in Hz)

The individual analoge pins are enabled / read by:

    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

In order to get the data at the given sampling rate you can register a callback
handler::
  
    >>> board.analog[0].register_callback(myCallback)
    
where myCallback(data) is then called every time when data has been received
and is timed by the arduino itself so is very precise.

If you use a pin more often, it can be worth it to use the ``get_pin`` method of the board. It let's you specify what pin you need by a string, composed of 'a' or 'd' (depending on wether you need an analog or digital pin), the pin number, and the mode ('i' for input, 'o' for output, 'p' for pwm). All seperated by ``:``. Eg. ``a:0:i`` for analog 0 as input, or ``d:3:p`` for digital pin 3 as pwm.::

    >>> analog_0 = board.get_pin('a:0:i')
    >>> analog_0.read()
    0.661440304938
    >>> pin3 = board.get_pin('d:3:p')
    >>> pin3.write(0.6)

Board layout
============

If you want to use a board with a different layout than the standard Arduino, or the Arduino Mega (for wich there exist the shortcut classes ``pyfirmata.Arduino`` and ``pyfirmata.ArduinoMega``), instantiate the Board class with a dictionary as the ``layout`` argument. This is the layout dict for the Mega for example::

    >>> mega = {
    ...         'digital' : tuple(x for x in range(54)),
    ...         'analog' : tuple(x for x in range(16)),
    ...         'pwm' : tuple(x for x in range(2,14)),
    ...         'use_ports' : True,
    ...         'disabled' : (0, 1, 14, 15) # Rx, Tx, Crystal
    ...         }

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

