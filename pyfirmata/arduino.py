import os
import sys

from boards import BOARDS
from serial.serialutil import SerialException
from pyfirmata import Board


# shortcut classes
class ArduinoBoard(Board):
    def __init__(self, *args, **kwargs):
        args = list(args)
        args.append(BOARDS[self.board_type])
        try:
            super(ArduinoBoard, self).__init__(*args, **kwargs)
        except SerialException:
            logging.error(
                'No device found at "%s". Make sure your Arduino is connected.' % args[0]
                )

    @property
    def board_type(self):
        raise Exception("ArduinoBoard class must implement board_type() method.")


class Arduino(ArduinoBoard):
    """
    A board that will set itself up as a normal Arduino.
    """
    def __str__(self):
        return 'Arduino %s on %s' % (self.name, self.sp.port)

    @property
    def board_type(self):
        return "arduino"


class ArduinoMega(Board):
    """
    A board that will set itself up as an Arduino Mega.
    """

    def __str__(self):
        return 'Arduino Mega %s on %s' % (self.name, self.sp.port)

    @property
    def board_type(self):
        return "ArduinoMega"