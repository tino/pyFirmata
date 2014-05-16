import time
import serial
import unittest
import platform

import mockup
import pyfirmata
from pyfirmata.boards import BOARDS


class BoardBaseTest(unittest.TestCase):

    FIRMWARE_NAME = "Firmware_name"
    FIRMWARE_VERSION = (2, 1)

    def setUp(self):
        # Test with the MockupSerial so no real connection is needed
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        # Set the wait time to a zero so we won't have to wait a couple of secs
        # each test
        pyfirmata.pyfirmata.BOARD_SETUP_WAIT_TIME = 0
        self.board = pyfirmata.Board('', BOARDS['arduino'])
        self.board._stored_data = [] # FIXME How can it be that a fresh instance sometimes still contains data?

    def tearDown(self):
        self.board.exit()
        pyfirmata.serial.Serial = serial.Serial


class MockupBoard(unittest.TestCase):
    """
    TestMockupBoardLayout is subclassed from TestBoardLayout and
    TestBoardMessages as it should pass the same tests, but with the
    MockupBoard.
    """

    FIRMWARE_NAME = "Firmware_name"
    FIRMWARE_VERSION = (2, 1)

    def setUp(self):
        self.board = mockup.MockupBoard('test', BOARDS['arduino'])

    def tearDown(self):
        self.board.exit()
        pyfirmata.serial.Serial = serial.Serial


class ArduinoDetection(unittest.TestCase):
    """
    Subclassing from TestBoardLayout and TestBoardMessages,
    in order to have the same tests. But it overwrites setUp(),
    this way a real any Arduino can be tested.
    """

    FIRMWARE_NAME = "StandardFirmata"
    FIRMWARE_VERSION = (2, 3)

    def setUp(self):
        system = platform.system()
        if system == 'Linux':
            # Rough estimation about where the device is. May fail.
            device = '/dev/ttyUSB0'
            self.board = pyfirmata.Board(device) # No Layout
        else:
            raise RuntimeError('System not supported.')

    def tearDown(self):
        self.board.exit()
        time.sleep(0.1)

