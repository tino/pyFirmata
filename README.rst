==========
arduPython
==========

arduPython is a Python interface for the `Firmata`_ protocol. It is fully
compatible with Firmata 2.1, and has some functionality of version 2.2. It runs
on Python 3.9 and 3.10.

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

If you install from source with ``python setup.py install``, don't forget to install ``pyserial`` as well.

.. _pip: http://www.pip-installer.org/en/latest/

Usage
=====

Basic usage::

    >>> from pyfirmata import Arduino, util
    >>> board = Arduino('/dev/tty.usbserial-A6008rIF')
    >>> board.digital[13].write(1)

To use analog ports, it is probably handy to start an iterator thread. Otherwise the board will keep sending data to your serial, until it overflows::

    >>> it = util.Iterator(board)
    >>> it.start()
    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

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

Ping support (pulseIn)
=======================

If you want to use ultrasonic range sensors that use a pulse to measure distance (like the very cheap and common ``HC-SR04``
- See `datasheet`,
you will need to use a pulseIn_ compatible Firmata on your card.

You can download it from the pulseIn_ branch of the Firmata repository:

Simply connect the sensor's ``Trig`` and ``Echo`` pins to a digital pin on your board.

.. _pulseIn: https://github.com/jgautier/arduino-1/tree/pulseIn
.. _datasheet: https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf

.. image:: ../../../blob/master/Examples/Figures/ping.png

And then use the ping method on the pin:

    >>> echo_pin = board.get_pin('d:7:o')
    >>> echo_pin.ping()
    1204

You can use the ``ping_time_to_distance`` function to convert
the result of the ping (echo time) in distance:

    >>> from pyfirmata.util import ping_time_to_distance
    >>> echo_pin = board.get_pin('d:7:o')
    >>> ping_time_to_distance(echo_pin.ping())
    20.4854580555607776

NOTE
====

The codes will only work if you download and load the `pulseIn`_:: code on the Arduino board! It has to be exactly the code quoted!

.. pulseIn: https://github.com/jgautier/arduino-1/tree/pulseIn

credits
========

- NeoPolus_:
- Tino_:

.. _NeoPolus: https://github.com/NeoPolus/pyFirmata
.. _Tino: https://github.com/tino/pyFirmata

links
=====

- Official Discord Server_:
- **My Discord Username:** *Aril Ogai#5646*

.. _Official Discord Server: https://discord.gg/nPejnfC3Nu
