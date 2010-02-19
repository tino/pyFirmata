import unittest
import serial
import time
from optparse import OptionParser

import pyfirmata
from pyfirmata import mockup
from pyfirmata.boards import BOARDS
from pyfirmata.util import to_7_bits

# This should be covered:
#
# This protocol uses the MIDI message format, but does not use the whole
# protocol.  Most of the command mappings here will not be directly usable in
# terms of MIDI controllers and synths.  It should co-exist with MIDI without
# trouble and can be parsed by standard MIDI interpreters.  Just some of the
# message data is used differently.
# 
# MIDI format: http://www.harmony-central.com/MIDI/Doc/table1.html
# 
#                              MIDI       
# type                command  channel    first byte            second byte 
# ---------------------------------------------------------------------------
# analog I/O message    0xE0   pin #      LSB(bits 0-6)         MSB(bits 7-13)
# digital I/O message   0x90   port       LSB(bits 0-6)         MSB(bits 7-13)
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
# 
# type                command  first byte       second byte      ...
# ----------------------------------------------------------------------------
# string                0x71   char *string ...
# firmware name/version 0x79   major version   minor version     char *name...


class BoardBaseTest(unittest.TestCase):
    def setUp(self):
        # Test with the MockupSerial so no real connection is needed
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        self.board = pyfirmata.Board('test')

class TestBoardMessages(BoardBaseTest):
    # TODO Test layout of Board Mega
    # TODO Test if messages written are correct...

    # First test the handlers
    def test_handle_analog_message(self):
        self.assertEqual(self.board.analog[3].read(), None)
        # Test it returns false with not enough params
        self.assertFalse(self.board._handle_analog_message([3, 127]))
        # This sould set it correctly. 1023 (127, 7 in to 7 bit bytes) is the
        # max value an analog pin will send and it should result in a value 1
        self.assertTrue(self.board._handle_analog_message([3, 127, 7]))
        self.assertEqual(self.board.analog[3].read(), 1)
        
    def test_handle_digital_message(self):
        self.assertEqual(self.board.digital[5].read(), None)
        # Test it returns false with not enough params
        self.assertFalse(self.board._handle_digital_message([5, 1]))
        # This should set it correctly.
        self.assertTrue(self.board._handle_digital_message([5, 1, 0]))
        self.assertEqual(self.board.digital[5].read(), 1)
        
    def test_handle_firmata_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.assertFalse(self.board._handle_report_version([1]))
        self.assertTrue(self.board._handle_report_version([2, 1]))
        self.assertEqual(self.board.firmata_version, (2, 1))
        
    # Now test the whole structure.
    
        
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
