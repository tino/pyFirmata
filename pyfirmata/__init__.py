from pyfirmata import *
from boards import BOARDS

__version__ = '0.9.5'  # Don't forget to change in setup.py!

# shortcut classes

class Arduino(Board):
    """
    A board that will set itself up as a normal Arduino.
    """
    def __init__(self, *args, **kwargs):
        args = list(args)
        args.append(BOARDS['arduino'])
        super(Arduino, self).__init__(*args, **kwargs)
        self.name = 'arduino'

    def __str__(self):
        return 'Arduino %s on %s' % (self.name, self.sp.port)


class ArduinoMega(Board):
    """
    A board that will set itself up as an Arduino Mega.
    """
    def __init__(self, *args, **kwargs):
        args = list(args)
        args.append(BOARDS['arduino_mega'])
        super(ArduinoMega, self).__init__(*args, **kwargs)
        self.name = 'arduino_mega'

    def __str__(self):
        return 'Arduino Mega %s on %s' % (self.name, self.sp.port)

class SparkCore(Board):
    """
    A board that will set itself up as a Spark Core
    """
    def __init__(self, *args, **kwargs):
        args = list(args)
        args.append(BOARDS['spark_core'])
        super(SparkCore, self).__init__(*args, **kwargs)
        self.name = 'spark_core'
