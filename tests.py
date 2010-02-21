import unittest
import serial
import time
from optparse import OptionParser

import pyfirmata
from pyfirmata import mockup
from pyfirmata.boards import BOARDS
from pyfirmata.util import to_7_bits

# Messages todo left:

# type                command  channel    first byte            second byte 
# ---------------------------------------------------------------------------
# report analog pin     0xC0   pin #      disable/enable(0/1)   - n/a -
# report digital port   0xD0   port       disable/enable(0/1)   - n/a -
# 
# sysex start           0xF0   
# set pin mode(I/O)     0xF4              pin # (0-127)         pin state(0=in)
# sysex end             0xF7   
# protocol version      0xF9              major version         minor version
# system reset          0xFF
#
# SysEx-based commands (0x00-0x7F) are used for an extended command set.


class BoardBaseTest(unittest.TestCase):
    def setUp(self):
        # Test with the MockupSerial so no real connection is needed
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        self.board = pyfirmata.Board('')
        self.board._stored_data = [] # FIXME How can it be that a fresh instance sometimes still contains data?
        
    def iterate(self, count):
        for i in range(count):
            self.board.iterate()
            
class TestBoardMessages(BoardBaseTest):
    # TODO Test layout of Board Mega

    # First test the handlers
    def test_handle_analog_message(self):
        self.board.analog[3].reporting = True
        self.assertEqual(self.board.analog[3].read(), None)
        # This sould set it correctly. 1023 (127, 7 in to 7 bit bytes) is the
        # max value an analog pin will send and it should result in a value 1
        self.assertTrue(self.board._handle_analog_message(3, 127, 7))
        self.assertEqual(self.board.analog[3].read(), 1.0)
        
    def test_handle_digital_message(self):
        # A digital message sets the value for a whole port. We will set pin
        # 5 (That is on port 0) to 1 to test if this is working.
        self.board.digital_ports[0].reporting = True
        self.board.digital[5]._mode = 0 # Set it to input
        # Create the mask
        mask = 0
        mask |= 1 << 5 # set the bit for pin 5 to to 1
        self.assertEqual(self.board.digital[5].read(), None)
        self.assertTrue(self.board._handle_digital_message(0, mask % 128, mask >> 7))
        self.assertEqual(self.board.digital[5].read(), True)
        
    def test_handle_report_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.assertTrue(self.board._handle_report_version(2, 1))
        self.assertEqual(self.board.firmata_version, (2, 1))
        
    # type                command  channel    first byte            second byte 
    # ---------------------------------------------------------------------------
    # analog I/O message    0xE0   pin #      LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_analog_message(self):
        self.assertEqual(self.board.analog[4].read(), None)
        self.assertEqual(self.board.analog[4].reporting, False)
        # Should do nothing as the pin isn't set to report
        self.board.sp.write([chr(pyfirmata.ANALOG_MESSAGE + 4), chr(127), chr(7)])
        self.iterate(3)
        self.assertEqual(self.board.analog[4].read(), None)
        self.board.analog[4].enable_reporting()
        self.board.sp.clear()
        # This should set analog port 4 to 1
        self.board.sp.write([chr(pyfirmata.ANALOG_MESSAGE + 4), chr(127), chr(7)])
        self.iterate(3)
        self.assertEqual(self.board.analog[4].read(), 1.0)
        self.board._stored_data = []
    
    # type                command  channel    first byte            second byte 
    # ---------------------------------------------------------------------------
    # digital I/O message   0x90   port       LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_digital_message(self):
        # A digital message sets the value for a whole port. We will set pin
        # 2 (on port 0) to 1 to test if this is working.
        self.board.digital[2].mode = pyfirmata.INPUT
        self.board.sp.clear() # clear mode sent over the wire.
        # Create the mask
        mask = 0
        mask |= 1 << 2 # set the bit for pin 2 to to 1
        self.assertEqual(self.board.digital[2].read(), None)
        self.board.sp.write([chr(pyfirmata.DIGITAL_MESSAGE + 0), chr(mask % 128), chr(mask >> 7)])
        self.iterate(3)
        self.assertEqual(self.board.digital[2].read(), True)
        
    # version report format
    # -------------------------------------------------
    # 0  version report header (0xF9) (MIDI Undefined)
    # 1  major version (0-127)
    # 2  minor version (0-127)
    def test_incoming_report_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.board.sp.write([chr(pyfirmata.REPORT_VERSION), chr(2), chr(1)])
        self.iterate(3)
        self.assertEqual(self.board.firmata_version, (2, 1))
        self.board._stored_data = []
        
class TestBoardLayout(BoardBaseTest):

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
        
    def tearDown(self):
        self.board.exit()
        pyfirmata.serial.Serial = serial.Serial
        
class TestMockupBoardLayout(TestBoardLayout, TestBoardMessages):
    """
    TestMockupBoardLayout is subclassed from TestBoardLayout and
    TestBoardMessages as it should pass the same tests, but with the
    MockupBoard.
    """
    def setUp(self):
        self.board = mockup.MockupBoard('test')


board_messages = unittest.TestLoader().loadTestsFromTestCase(TestBoardMessages)
board_layout = unittest.TestLoader().loadTestsFromTestCase(TestBoardLayout)
default = unittest.TestSuite([board_messages, board_layout])
mockup_suite = unittest.TestLoader().loadTestsFromTestCase(TestMockupBoardLayout)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m", "--mockup", dest="mockup", action="store_true",
        help="Also run the mockup tests")
    options, args = parser.parse_args()
    if not options.mockup:
        print "Running normal suite. Also consider running the live (-l, --live) \
                and mockup (-m, --mockup) suites"
        unittest.TextTestRunner(verbosity=3).run(default)
    if options.mockup:
        print "Running the mockup test suite"
        unittest.TextTestRunner(verbosity=2).run(mockup_suite)
