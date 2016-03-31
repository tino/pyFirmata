from __future__ import division
from __future__ import unicode_literals
import threading
import time
import os

import serial

import pyfirmata
from .boards import BOARDS


def get_the_board(layout=BOARDS['arduino'], base_dir='/dev/', identifier='tty.usbserial', baudrate=57600, name=None, timeout=None,):
    """
    Helper function to get the one and only board connected to the computer
    running this. It assumes a normal arduino layout, but this can be
    overriden by passing a different layout dict as the ``layout`` parameter.
    ``base_dir`` and ``identifier`` are overridable as well. It will raise an
    IOError if it can't find a board, on a serial, or if it finds more than
    one.
    """
    boards = []
    for device in os.listdir(base_dir):
        if device.startswith(identifier):
            try:
                board = pyfirmata.Board(os.path.join(base_dir, device), 
                                        layout, baudrate=baudrate, name=name, 
                                        timeout=timeout)
            except serial.SerialException:
                pass
            else:
                boards.append(board)
    if len(boards) == 0:
        raise IOError("No boards found in {0} with identifier {1}".format(base_dir, identifier))
    elif len(boards) > 1:
        raise IOError("More than one board found!")
    return boards[0]


class Iterator(threading.Thread):
    def __init__(self, board):
        super(Iterator, self).__init__()
        self.board = board

        # For proper exit even when Board.exit() doesn't get called
        # we need to flag this thread as 'daemon'.
        #   "The significance of this flag is that the entire Python
        #    program exits when only daemon threads are left."
        # This way Python won't hang at exit, will just warn of
        # an exception at shutdown.
        # Anyway it's better to call Board.exit() or use
        # a "with board: ..." block to avoid this warning.
        self.daemon = True

    def run(self):
        while 1:
            try:
                while self.board.bytes_available():
                    self.board.iterate()
                time.sleep(0.001)
            except (AttributeError, serial.SerialException, OSError) as e:
                # this way we can kill the thread by setting the board object
                # to None, or when the serial port is closed by board.exit()
                break
            except Exception as e:
                # catch 'error: Bad file descriptor'
                # iterate may be called while the serial port is being closed,
                # causing an "error: (9, 'Bad file descriptor')"
                if getattr(e, 'errno', None) == 9:
                    break
                try:
                    if e[0] == 9:
                        break
                except (TypeError, IndexError):
                    pass
                raise


def to_two_bytes(integer):
    """
    Breaks an integer into two 7 bit bytes.
    """
    if integer > 32767:
        raise ValueError("Can't handle values bigger than 32767 (max for 2 bits)")
    return bytearray([integer % 128, integer >> 7])


def from_two_bytes(bytes):
    """
    Return an integer from two 7 bit bytes.
    """
    lsb, msb = bytes
    try:
        # Usually bytes have been converted to integers with ord already
        return msb << 7 | lsb
    except TypeError:
        # But add this for easy testing
        # One of them can be a string, or both
        try:
            lsb = ord(lsb)
        except TypeError:
            pass
        try:
            msb = ord(msb)
        except TypeError:
            pass
        return msb << 7 | lsb


def two_byte_iter_to_str(bytes):
    """
    Return a string made from a list of two byte chars.
    """
    bytes = list(bytes)
    chars = bytearray()
    while bytes:
        lsb = bytes.pop(0)
        try:
            msb = bytes.pop(0)
        except IndexError:
            msb = 0x00
        chars.append(from_two_bytes([lsb, msb]))
    return chars.decode()


def str_to_two_byte_iter(string):
    """
    Return a iter consisting of two byte chars from a string.
    """
    bstring = string.encode()
    bytes = bytearray()
    for char in bstring:
        bytes.append(char)
        bytes.append(0)
    return bytes


def break_to_bytes(value):
    """
    Breaks a value into values of less than 255 that form value when multiplied.
    (Or almost do so with primes)
    Returns a tuple
    """
    if value < 256:
        return (value,)
    c = 256
    least = (0, 255)
    for i in range(254):
        c -= 1
        rest = value % c
        if rest == 0 and value / c < 256:
            return (c, int(value / c))
        elif rest == 0 and value / c > 255:
            parts = list(break_to_bytes(value / c))
            parts.insert(0, c)
            return tuple(parts)
        else:
            if rest < least[1]:
                least = (c, rest)
    return (c, int(value / c))


def pin_list_to_board_dict(pinlist):
    """
    Capability Response codes:
        INPUT:  0, 1
        OUTPUT: 1, 1
        ANALOG: 2, 10
        PWM:    3, 8
        SERV0:  4, 14
        I2C:    6, 1
    """

    board_dict = {
        'digital': [],
        'analog': [],
        'pwm': [],
        'servo': [],  # 2.2 specs
        #'i2c': [],  # 2.3 specs
        'disabled': [],
    }
    for i, pin in enumerate(pinlist):
        pin.pop()  # removes the 0x79 on end
        if not pin:
            board_dict['disabled'] += [i]
            board_dict['digital'] += [i]
            continue

        for j, _ in enumerate(pin):
            # Iterate over evens
            if j % 2 == 0:
                # This is safe. try: range(10)[5:50]
                if pin[j:j + 4] == [0, 1, 1, 1]:
                    board_dict['digital'] += [i]

                if pin[j:j + 2] == [2, 10]:
                    board_dict['analog'] += [i]

                if pin[j:j + 2] == [3, 8]:
                    board_dict['pwm'] += [i]

                if pin[j:j + 2] == [4, 14]:
                    board_dict['servo'] += [i]

                # Desable I2C
                if pin[j:j + 2] == [6, 1]:
                    pass

    # We have to deal with analog pins:
    # - (14, 15, 16, 17, 18, 19)
    # + (0, 1, 2, 3, 4, 5)
    diff = set(board_dict['digital']) - set(board_dict['analog'])
    board_dict['analog'] = [n for n, _ in enumerate(board_dict['analog'])]

    # Digital pin problems:
    #- (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
    #+ (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)

    board_dict['digital'] = [n for n, _ in enumerate(diff)]
    # Based on lib Arduino 0017
    board_dict['servo'] = board_dict['digital']

    # Turn lists into tuples
    # Using dict for Python 2.6 compatibility
    board_dict = dict([
        (key, tuple(value))
        for key, value
        in board_dict.items()
    ])

    return board_dict


def ping_time_to_distance(time, calibration=None, distance_units='cm'):
    """
    Calculates the distance (in cm) given the time of a ping echo.

    By default it uses the speed of sound (at sea level = 340.29 m/s)
    to calculate the distance, but a list of calibrated points can
    be used to calculate the distance using linear interpolation.

    :arg calibration: A sorted list of (time, distance) tuples to calculate
                        the distance using linear interpolation between the
                        two closest points.
                        Example (for a HC-SR04 ultrasonic ranging sensor):
                        [(680.0, 10.0), (1460.0, 20.0), (2210.0, 30.0)]
    """
    if not time: 
        return 0
    if not calibration: # Standard calculation using speed of sound.
        # 1 (second) / 340.29 (speed of sound in m/s) = 0.00293866995 metres
        # distance = duration (microseconds) / 29.38 / 2 (go and back)
        distance = time / 29.3866995 / 2
    else: # Linear interpolation between two calibration points.
        a = (0, 0)
        b = calibration[-1]
        for c in calibration:
            if c[0] < time: a = c
            if c[0] > time: b = c; break
        if a == b:
            a = calibration[-2]
        distance = a[1] + (b[1] - a[1]) * ((time - a[0]) / (b[0] - a[0]))
    return distance