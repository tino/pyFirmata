==========
pyFirmata2
==========

PyFirmata2 turns your Arduino into a data acquisition card controlled by Python.

Up to 1kHz precise sampling at the analogue ports for digital filtering.

Just upload the default firmata sketch into your Arduino and you are all set.

pyFirmata2 is an updated version of pyFirmata which *replaces loops
with callbacks*. Instead of unreliable "sleep" commands in a loop the
Python application registers callbacks which are then called every
time after new data has arrived. This means for the analogue
channels the callbacks are called at the specified sampling rate
while the digital ports call the callback functions after
a state change at the port (from 0 to 1 or 1 to 0).

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

Please go to https://github.com/berndporr/pyFirmata2 for the
documentation and in particular the example code.


Example code
============

It's strongly recommended to check out the example code at
https://github.com/berndporr/pyFirmata2/tree/master/examples
to see how the callbacks work.


Credits
=======

The original pyFirmata was written by Tino de Bruijn.
The realtime sampling / callback has been added by Bernd Porr.
