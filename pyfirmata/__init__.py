from .pyfirmata import *

__version__ = '0.9.4'
__all__ = ['pyfirmata', 'boards', 'util']
# shortcut classes

class Arduino(Board):
    """
    A board that wil set itself up as a normal Arduino.
    """
    def __init__(self, *args, **kwargs):
        args = list(args)
        args.append(BOARDS['arduino'])
        super(Arduino, self).__init__(*args, **kwargs)
        
    def __str__(self):
        return "Arduino {0.name} on {0.sp.port}".format(self)
    
class ArduinoMega(Board):
    """
    A board that wil set itself up as an Arduino Mega.
    """
    def __init__(self, *args, **kwargs):
        args = list(args)
        args.append(BOARDS['arduino_mega'])
        super(ArduinoMega, self).__init__(*args, **kwargs)
    
    def __str__(self):
        return "Arduino Mega {0.name} on {0.sp.port}".format(self)
