from __future__ import division
from __future__ import unicode_literals
import threading
import time
import os

import serial

import pyfirmata
from .boards import BOARDS


def get_the_board(layout=BOARDS['arduino'], base_dir='/dev/', identifier='tty.usbserial',):
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
                board = pyfirmata.Board(os.path.join(base_dir, device), layout)
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
