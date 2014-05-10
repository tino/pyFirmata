import abc

import pyfirmata
from pyfirmata.boards import BOARDS, pinList2boardDict
import mockup

class TestBoardLayout(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self):
        pass

    def test_layout_arduino(self):
        self.assertEqual(len(BOARDS['arduino']['digital']), len(self.board.digital))
        self.assertEqual(len(BOARDS['arduino']['analog']), len(self.board.analog))

    def test_layout_arduino_mega(self):
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        mega = pyfirmata.Board('', BOARDS['arduino_mega'])
        self.assertEqual(len(BOARDS['arduino_mega']['digital']), len(mega.digital))
        self.assertEqual(len(BOARDS['arduino_mega']['analog']), len(mega.analog))

    def test_pwm_layout(self):
        pins = []
        for pin in self.board.digital:
            if pin.PWM_CAPABLE:
                pins.append(self.board.get_pin('d:%d:p' % pin.pin_number))
        for pin in pins:
            self.assertEqual(pin.mode, pyfirmata.PWM)
            self.assertTrue(pin.pin_number in BOARDS['arduino']['pwm'])
        self.assertTrue(len(pins) == len(BOARDS['arduino']['pwm']))


    def test_get_pin_digital(self):
        pin = self.board.get_pin('d:13:o')
        self.assertEqual(pin.pin_number, 13)
        self.assertEqual(pin.mode, pyfirmata.OUTPUT)
        self.assertEqual(pin.port.port_number, 1)
        self.assertEqual(pin.port.reporting, False)

    def test_get_pin_analog(self):
        pin = self.board.get_pin('a:5:i')
        self.assertEqual(pin.pin_number, 5)
        self.assertEqual(pin.reporting, True)
        self.assertEqual(pin.value, None)

    def test_pinList2boardDict(self):
        # Arduino's Example: (ATMega328P-PU)
        pinList = [
            [127],
            [127],
            [0, 1, 1, 1, 4, 14, 127],
            [0, 1, 1, 1, 3, 8, 4, 14, 127],
            [0, 1, 1, 1, 4, 14, 127],
            [0, 1, 1, 1, 3, 8, 4, 14, 127],
            [0, 1, 1, 1, 3, 8, 4, 14, 127],
            [0, 1, 1, 1, 4, 14, 127],
            [0, 1, 1, 1, 4, 14, 127],
            [0, 1, 1, 1, 3, 8, 4, 14, 127],
            [0, 1, 1, 1, 3, 8, 4, 14, 127],
            [0, 1, 1, 1, 3, 8, 4, 14, 127],
            [0, 1, 1, 1, 4, 14, 127],
            [0, 1, 1, 1, 4, 14, 127],
            [0, 1, 1, 1, 2, 10, 127],
            [0, 1, 1, 1, 2, 10, 127],
            [0, 1, 1, 1, 2, 10, 127],
            [0, 1, 1, 1, 2, 10, 127],
            [0, 1, 1, 1, 2, 10, 6, 1, 127],
            [0, 1, 1, 1, 2, 10, 6, 1, 127],
        ]

        boardDict = pinList2boardDict(pinList)
        test_layout = BOARDS['arduino']

        for key in test_layout.keys():
            print boardDict[key], test_layout[key]
            self.assertEqual(boardDict[key], test_layout[key])

    def tearDown(self):
        self.board.exit()
        pyfirmata.serial.Serial = serial.Serial

