=======
Changes
=======

Version 1.1.x
=============

1.10 - 10/09/2018
-----------------

- Added function ``samplingOn`` which starts contiouns data acquisition in the background
  with the optional parameter ``samplingOn(samplingRateHz)`` to set the sampling rate
  of the arduino and ``samplingOff`` to disable it again.
- Added function ``register_callback`` which is called every time after new data has
  arrived at the given sampling rate.


Version 1.0.x
=============

1.0.3 - 17/05/2015
------------------

- Pass ``timeout`` parameter on board trough to ``pyserial.Serial``.
- Added this change list.

1.0.2 - 17/01/2015
------------------

- Configure ``bumpversion``.
- Update to-do list.

1.0.1 - 17/01/2015
------------------

- Added Firmata's "Capability Query", that allows to auto setup a board. (This probably deserved a minor version bump...)
- Start distributing as wheels

1.0.0 - 04/01/2015
------------------

- Added Python 3 support
- Testing on Python 2.6 is dropped, but it might still work. Not actively supported though.
