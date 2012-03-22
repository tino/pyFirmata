import unittest
import doctest
import serial
from itertools import chain
import pyfirmata
from pyfirmata import mockup
from pyfirmata.boards import BOARDS
from pyfirmata.util import str_to_two_byte_iter, to_two_bytes

# Messages todo left:

# type                command  channel    first byte            second byte
# ---------------------------------------------------------------------------
# set pin mode(I/O)     0xF4              pin # (0-127)         pin state(0=in)
# system reset          0xFF

class BoardBaseTest(unittest.TestCase):
    def setUp(self):
        # Test with the MockupSerial so no real connection is needed
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        self.board = pyfirmata.Board('', BOARDS['arduino'])
        self.board._stored_data = [] # FIXME How can it be that a fresh instance sometimes still contains data?


class TestBoardMessages(BoardBaseTest):
    # TODO Test layout of Board Mega
    def assert_serial(self, *list_of_chrs):
        res = self.board.sp.read()
        serial_msg = res
        while res:
            res = self.board.sp.read()
            serial_msg += res
        self.assertEqual(''.join(list(list_of_chrs)), serial_msg)

    # First test the handlers
    def test_handle_analog_message(self):
        self.board.analog[3].reporting = True
        self.assertEqual(self.board.analog[3].read(), None)
        # This sould set it correctly. 1023 (127, 7 in to 7 bit bytes) is the
        # max value an analog pin will send and it should result in a value 1
        self.board._handle_analog_message(3, 127, 7)
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
        self.board._handle_digital_message(0, mask % 128, mask >> 7)
        self.assertEqual(self.board.digital[5].read(), True)

    def test_handle_report_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.board._handle_report_version(2, 1)
        self.assertEqual(self.board.firmata_version, (2, 1))

    def test_handle_report_firmware(self):
        self.assertEqual(self.board.firmware, None)
        data = [2, 1] + str_to_two_byte_iter('Firmware_name')
        self.board._handle_report_firmware(*data)
        self.assertEqual(self.board.firmware, 'Firmware_name')
        self.assertEqual(self.board.firmware_version, (2, 1))

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # analog I/O message    0xE0   pin #      LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_analog_message(self):
        self.assertEqual(self.board.analog[4].read(), None)
        self.assertEqual(self.board.analog[4].reporting, False)
        # Should do nothing as the pin isn't set to report
        self.board.sp.write([chr(pyfirmata.ANALOG_MESSAGE + 4), chr(127), chr(7)])
        self.board.iterate()
        self.assertEqual(self.board.analog[4].read(), None)
        self.board.analog[4].enable_reporting()
        self.board.sp.clear()
        # This should set analog port 4 to 1
        self.board.sp.write([chr(pyfirmata.ANALOG_MESSAGE + 4), chr(127), chr(7)])
        self.board.iterate()
        self.assertEqual(self.board.analog[4].read(), 1.0)
        self.board._stored_data = []

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # digital I/O message   0x90   port       LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_digital_message(self):
        # A digital message sets the value for a whole port. We will set pin
        # 9 (on port 1) to 1 to test if this is working.
        self.board.digital[9].mode = pyfirmata.INPUT
        self.board.sp.clear() # clear mode sent over the wire.
        # Create the mask
        mask = 0
        mask |= 1 << (9 - 8) # set the bit for pin 9 to to 1
        self.assertEqual(self.board.digital[9].read(), None)
        self.board.sp.write([chr(pyfirmata.DIGITAL_MESSAGE + 1), chr(mask % 128), chr(mask >> 7)])
        self.board.iterate()
        self.assertEqual(self.board.digital[9].read(), True)

    # version report format
    # -------------------------------------------------
    # 0  version report header (0xF9) (MIDI Undefined)
    # 1  major version (0-127)
    # 2  minor version (0-127)
    def test_incoming_report_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.board.sp.write([chr(pyfirmata.REPORT_VERSION), chr(2), chr(1)])
        self.board.iterate()
        self.assertEqual(self.board.firmata_version, (2, 1))

    # Receive Firmware Name and Version (after query)
    # 0  START_SYSEX (0xF0)
    # 1  queryFirmware (0x79)
    # 2  major version (0-127)
    # 3  minor version (0-127)
    # 4  first 7-bits of firmware name
    # 5  second 7-bits of firmware name
    # x  ...for as many bytes as it needs)
    # 6  END_SYSEX (0xF7)
    def test_incoming_report_firmware(self):
        self.assertEqual(self.board.firmware, None)
        self.assertEqual(self.board.firmware_version, None)
        msg = [chr(pyfirmata.START_SYSEX),
               chr(pyfirmata.REPORT_FIRMWARE),
               chr(2),
               chr(1)] + str_to_two_byte_iter('Firmware_name') + \
              [chr(pyfirmata.END_SYSEX)]
        self.board.sp.write(msg)
        self.board.iterate()
        self.assertEqual(self.board.firmware, 'Firmware_name')
        self.assertEqual(self.board.firmware_version, (2, 1))

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # report analog pin     0xC0   pin #      disable/enable(0/1)   - n/a -
    def test_report_analog(self):
        self.board.analog[1].enable_reporting()
        self.assert_serial(chr(0xC0 + 1), chr(1))
        self.assertTrue(self.board.analog[1].reporting)
        self.board.analog[1].disable_reporting()
        self.assert_serial(chr(0xC0 + 1), chr(0))
        self.assertFalse(self.board.analog[1].reporting)

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # report digital port   0xD0   port       disable/enable(0/1)   - n/a -
    def test_report_digital(self):
        # This should enable reporting of whole port 1
        self.board.digital[8]._mode = pyfirmata.INPUT # Outputs can't report
        self.board.digital[8].enable_reporting()
        self.assert_serial(chr(0xD0 + 1), chr(1))
        self.assertTrue(self.board.digital_ports[1].reporting)
        self.board.digital[8].disable_reporting()
        self.assert_serial(chr(0xD0 + 1), chr(0))

    # Generic Sysex Message
    # 0     START_SYSEX (0xF0)
    # 1     sysex command (0x00-0x7F)
    # x     between 0 and MAX_DATA_BYTES 7-bit bytes of arbitrary data
    # last  END_SYSEX (0xF7)
    def test_send_sysex_message(self):
        # 0x79 is queryFirmware, but that doesn't matter for now
        self.board.send_sysex(0x79, [1, 2, 3])
        sysex = (chr(0xF0), chr(0x79), chr(1), chr(2), chr(3), chr(0xF7))
        self.assert_serial(*sysex)

    def test_send_sysex_to_big_data(self):
        self.assertRaises(ValueError, self.board.send_sysex, 0x79, [256, 1])

    def test_receive_sysex_message(self):
        sysex = (chr(0xF0), chr(0x79), chr(2), chr(1), 'a', '\x00', 'b',
            '\x00', 'c', '\x00', chr(0xF7))
        self.board.sp.write(sysex)
        while len(self.board.sp):
            self.board.iterate()
        self.assertEqual(self.board.firmware_version, (2, 1))
        self.assertEqual(self.board.firmware, 'abc')

    def test_too_much_data(self):
        """
        When we send random bytes, before or after a command, they should be
        ignored to prevent cascading errors when missing a byte.
        """
        self.board.analog[4].enable_reporting()
        self.board.sp.clear()
        # Crap
        self.board.sp.write([chr(i) for i in range(10)])
        # This should set analog port 4 to 1
        self.board.sp.write([chr(pyfirmata.ANALOG_MESSAGE + 4), chr(127), chr(7)])
        # Crap
        self.board.sp.write([chr(10-i) for i in range(10)])
        while len(self.board.sp):
            self.board.iterate()
        self.assertEqual(self.board.analog[4].read(), 1.0)

    # Servo config
    # --------------------
    # 0  START_SYSEX (0xF0)
    # 1  SERVO_CONFIG (0x70)
    # 2  pin number (0-127)
    # 3  minPulse LSB (0-6)
    # 4  minPulse MSB (7-13)
    # 5  maxPulse LSB (0-6)
    # 6  maxPulse MSB (7-13)
    # 7  END_SYSEX (0xF7)
    #
    # then sets angle
    # 8  analog I/O message (0xE0)
    # 9  angle LSB
    # 10 angle MSB
    def test_servo_config(self):
        self.board.servo_config(2)
        data = chain([chr(0xF0), chr(0x70), chr(2)], to_two_bytes(544),
            to_two_bytes(2400), chr(0xF7), chr(0xE0 + 2), chr(0), chr(0))
        self.assert_serial(*data)

    def test_servo_config_min_max_pulse(self):
        self.board.servo_config(2, 600, 2000)
        data = chain([chr(0xF0), chr(0x70), chr(2)], to_two_bytes(600),
            to_two_bytes(2000), chr(0xF7), chr(0xE0 + 2), chr(0), chr(0))
        self.assert_serial(*data)

    def test_servo_config_min_max_pulse_angle(self):
        self.board.servo_config(2, 600, 2000, angle=90)
        data = chain([chr(0xF0), chr(0x70), chr(2)], to_two_bytes(600),
            to_two_bytes(2000), chr(0xF7))
        angle_set = [chr(0xE0 + 2), chr(90 % 128),
            chr(90 >> 7)] # Angle set happens through analog message
        data = list(data) + angle_set
        self.assert_serial(*data)

    def test_servo_config_invalid_pin(self):
        self.assertRaises(IOError, self.board.servo_config, 1)

    def test_set_mode_servo(self):
        p = self.board.digital[2]
        p.mode = pyfirmata.SERVO
        data = chain([chr(0xF0), chr(0x70), chr(2)], to_two_bytes(544),
            to_two_bytes(2400), chr(0xF7), chr(0xE0 + 2), chr(0), chr(0))
        self.assert_serial(*data)


class TestBoardLayout(BoardBaseTest):

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
        self.board = mockup.MockupBoard('test', BOARDS['arduino'])


class RegressionTests(BoardBaseTest):

    def test_correct_digital_input_first_pin_issue_9(self):
        """
        The first pin on the port would always be low, even if the mask said
        it to be high.
        """
        pin = self.board.get_pin('d:8:i')
        mask = 0
        mask |= 1 << 0 # set pin 0 high
        self.board._handle_digital_message(pin.port.port_number,
            mask % 128, mask >> 7)
        self.assertEqual(pin.value, True)

    def test_handle_digital_inputs(self):
        """
        Test if digital inputs are correctly updated.
        """
        for i in range(8, 16): # pins of port 1
            if not bool(i%2) and i != 14: # all even pins
                self.board.digital[i].mode = pyfirmata.INPUT
                self.assertEqual(self.board.digital[i].value, None)
        mask = 0
        # Set the mask high for the first 4 pins
        for i in range(4):
            mask |= 1 << i
        self.board._handle_digital_message(1, mask % 128, mask >> 7)
        self.assertEqual(self.board.digital[8].value, True)
        self.assertEqual(self.board.digital[9].value, None)
        self.assertEqual(self.board.digital[10].value, True)
        self.assertEqual(self.board.digital[11].value, None)
        self.assertEqual(self.board.digital[12].value, False)
        self.assertEqual(self.board.digital[13].value, None)


board_messages = unittest.TestLoader().loadTestsFromTestCase(TestBoardMessages)
board_layout = unittest.TestLoader().loadTestsFromTestCase(TestBoardLayout)
regression = unittest.TestLoader().loadTestsFromTestCase(RegressionTests)
default = unittest.TestSuite([board_messages, board_layout, regression])
mockup_suite = unittest.TestLoader().loadTestsFromTestCase(TestMockupBoardLayout)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-m", "--mockup", dest="mockup", action="store_true",
        help="Also run the mockup tests")
    options, args = parser.parse_args()
    if not options.mockup:
        print "Running normal suite. Also consider running the mockup (-m, --mockup) suite"
        unittest.TextTestRunner(verbosity=3).run(default)
        from pyfirmata import util
        print "Running doctests for pyfirmata.util. (No output = No errors)"
        doctest.testmod(util)
        print "Done running doctests"
    if options.mockup:
        print "Running the mockup test suite"
        unittest.TextTestRunner(verbosity=2).run(mockup_suite)
