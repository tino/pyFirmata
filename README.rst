=========
pyFirmata
=========

pyFirmata is a Python interface for the `Firmata`_ protocol. It is fully
compatible with Firmata 2.1, and has some functionality of version 2.2. It runs
on Python 2.7, 3.3 and 3.4.

.. _Firmata: http://firmata.org

Test status:

.. image:: https://travis-ci.org/tino/pyFirmata.png?branch=master
    :target: https://travis-ci.org/tino/pyFirmata


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

To use analog ports, it is probably handy to start an iterator thread.
Otherwise the board will keep sending data to your serial, until it overflows::

    >>> it = util.Iterator(board)
    >>> it.start()
    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

A better option is to use a ``with`` block. This way the Iterator is managed 
automagically, and you don't have to take care of calling ``board.exit()``
to stop the Iterator thread when you're done::

    >>> with board:
    >>>     board.analog[0].enable_reporting()
    >>>     board.analog[0].read()
    0.661440304938

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

Ping (pulseIn) support
======================

If you want to use ultrasonic ranging sensors that use a pulse to
measure distances (like the very cheap and common ``HC-SR04``
- see http://www.micropik.com/PDF/HCSR04.pdf),
you'll need to use a``pulseIn`` compatible Firmata in your board.

You can download it from the ``pulseIn`` branch
of the Firmata repository:
https://github.com/jgautier/arduino-1/tree/pulseIn

Just plug the sensor ``Trig`` and ``Echo`` pins
to a digital pin on your board.

.. image:: examples/ping.png

And then use the ping method on the pin:

    >>> echo_pin = board.get_pin('d:7:o')
    >>> echo_pin.ping()
    1204

You can use the ``ping_time_to_distance`` function to convert
the ping result (echo time) into distance:

    >>> from pyfirmata.util import ping_time_to_distance
    >>> echo_pin = board.get_pin('d:7:o')
    >>> ping_time_to_distance(echo_pin.ping())
    20.485458055607776

Todo
====

The next things on my list are to implement the new protocol changes in
firmata:

- Pin State Query, which allows it to populate on-screen controls with an
  accurate representation of the hardware's configuration
  (http://firmata.org/wiki/Proposals#Pin_State_Query_.28added_in_version_2.2.29)
