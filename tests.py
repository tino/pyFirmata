from __future__ import division
from __future__ import unicode_literals
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
        # Set the wait time to a zero so we won't have to wait a couple of secs
        # each test
        pyfirmata.pyfirmata.BOARD_SETUP_WAIT_TIME = 0
        self.board = pyfirmata.Board('BoardBaseTest_board', BOARDS['arduino'])
        self.board._stored_data = [] 
        # FIXME How can it be that a fresh instance sometimes still contains data?
        # @ FIXME: this could be because closing a board instance did not really
        # remove the references to the Pin/Port/Board objects. The modified
        # pyfirmata.board.exit() function should solve this issue.

    def tearDown(self):
        self.board.exit()
        

class TestBoardMessages(BoardBaseTest):
    # TODO Test layout of Board Mega
    def assert_serial(self, *incoming_bytes):
        serial_msg = bytearray()
        res = self.board.sp.read()
        while res is not None:
            serial_msg += res
            res = self.board.sp.read()
        self.assertEqual(bytearray(incoming_bytes), serial_msg)

    # First test the handlers
    def test_handle_analog_message(self):
        self.board.analog_pins[3].mode = pyfirmata.ANALOG
        self.assertEqual(self.board.analog_pins[3].read(), None)
        # The following command sets analog value to 1.
        # The max value an analog pin will send is 1023 ([127, 7] in 
        # two 7-bit bytes), and should result in a value of 1.
        self.board._handle_analog_message(3, 127, 7)
        self.assertEqual(self.board.analog_pins[3].read(), 1.0)
        # test that the correct bytes have been sent to Firmata.
        # The first command sent is SET_PIN_MODE, should be: 0xF4, 17, 2
        # The second command sent is REPORT_ANALOG, should be: 0xC0 + 3, 1
        self.assertEqual(list(self.board.sp), [0xF4, 17, 2, 0xC0 + 3, 1])
        

    def test_handle_digital_message(self):
        # A digital message sets the value for a whole port. We will set pin
        # 5 (That is on port 0) to 1 to test if this is working.
        self.board.ports[0].reporting = True
        self.board.pins[5].mode = 0 # Set it to input
        # Create the mask
        mask = 0
        mask |= 1 << 5 # set the bit for pin 5 to to 1
        self.board.pins[5].taken = True
        self.assertEqual(self.board.pins[5].read(), None)
        self.board._handle_digital_message(0, mask % 128, mask >> 7)
        self.assertEqual(self.board.pins[5].read(), True)
        # test that the correct bytes have been sent to Firmata:
        # The first command sent is SET_PIN_MODE, should be: 0xF4, 5, 0
        # The second command sent is REPORT_DIGITAL, should be: 0xD0, 1
        self.assertEqual(list(self.board.sp), [0xF4, 5, 0, 0xD0, 1])
        
        

    def test_handle_report_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.board._handle_report_version(2, 1)
        self.assertEqual(self.board.firmata_version, (2, 1))

    def test_handle_report_firmware(self):
        self.assertEqual(self.board.firmware, None)
        data = bytearray([2, 1])
        data.extend(str_to_two_byte_iter('Firmware_name'))
        self.board._handle_report_firmware(*data)
        self.assertEqual(self.board.firmware, 'Firmware_name')
        self.assertEqual(self.board.firmware_version, (2, 1))

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # analog I/O message    0xE0   pin #      LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_analog_message(self):
        # prepare the pin to receive analog signals
        self.board.analog_pins[4].mode = pyfirmata.ANALOG # send 0xF4 18 02
                                                          # also, send 0xC4 01 (enable reporting)
        # The pin should not have any value by now, it is only initialized
        self.assertEqual(self.board.analog_pins[4].read(), None)
        # Now let's clear the deque, and mimick an incoming analog signal
        self.board.sp.clear()
        self.board.sp.write([pyfirmata.ANALOG_MESSAGE + 4, 127, 7]) # 0xE0+4, 127, 7
        self.board.iterate()
        # Read should be (MSB, LSB) = (127, 7) = 1023, value = 1023/1023 = 1.0
        self.assertEqual(self.board.analog_pins[4].read(), 1.0)
        # Clear the deque again, and send another incoming analog signal
        self.board.sp.clear()
        self.board.sp.write([pyfirmata.ANALOG_MESSAGE + 4, 110, 5])
        self.board.iterate()
        # Read should be (MSB, LSB) = (110, 5) = 750, value = 750/1023
        self.assertEqual(self.board.analog_pins[4].read(), 0.7331)

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # digital I/O message   0x90   port       LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_digital_message(self):
        # A digital message sets the value for a whole port. We will set pin
        # 9 (on port 1) to 1 to test if this is working.
        self.board.pins[9].mode = pyfirmata.INPUT   # send 0xF4, 9, 0
        self.board.sp.clear() # clear mode sent over the wire.
        # Create the mask
        mask = 0
        mask |= 1 << (9 - 8) # set the bit for pin 9 to to 1
        self.assertEqual(self.board.pins[9].read(), None)
        self.board.sp.write([pyfirmata.DIGITAL_MESSAGE + 1, mask % 128, mask >> 7])
        self.board.iterate()
        self.assertEqual(self.board.pins[9].read(), True)

    # version report format
    # -------------------------------------------------
    # 0  version report header (0xF9) (MIDI Undefined)
    # 1  major version (0-127)
    # 2  minor version (0-127)
    def test_incoming_report_version(self):
        self.assertEqual(self.board.firmata_version, None)
        self.board.sp.write([pyfirmata.REPORT_VERSION, 2, 1])
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
        msg = [pyfirmata.START_SYSEX,
               pyfirmata.REPORT_FIRMWARE,
               2,
               1] + list(str_to_two_byte_iter('Firmware_name')) + \
              [pyfirmata.END_SYSEX]
        self.board.sp.write(msg)
        self.board.iterate()
        self.assertEqual(self.board.firmware, 'Firmware_name')
        self.assertEqual(self.board.firmware_version, (2, 1))

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # report analog pin     0xC0   pin #      disable/enable(0/1)   - n/a -
    def test_report_analog(self):
        self.board.analog_pins[1].mode = pyfirmata.ANALOG   # send 0xF4 15, 2, then 0xC1, 1 to enable reporting
        # Note that when Analog mode is set, reporting is automatically enabled
        self.assertTrue(self.board.analog_pins[1].reporting)
        self.board.sp.clear()
        self.board.analog_pins[1].disable_reporting()
        self.assert_serial(0xC0 + 1, 0)
        self.assertFalse(self.board.analog_pins[1].reporting)

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # report digital port   0xD0   port       disable/enable(0/1)   - n/a -
    def test_report_digital(self):
        # This should enable reporting of whole port 1
        self.board.pins[8].mode = pyfirmata.INPUT # Outputs can't report
        # clear the deque
        self.board.sp.clear()
        self.board.pins[8].enable_reporting()
        self.assert_serial(0xD0 + 1, 1)
        self.assertTrue(self.board.ports[1].reporting)
        self.board.pins[8].disable_reporting()
        self.assert_serial(0xD0 + 1, 0)

    # Generic Sysex Message
    # 0     START_SYSEX (0xF0)
    # 1     sysex command (0x00-0x7F)
    # x     between 0 and MAX_DATA_BYTES 7-bit bytes of arbitrary data
    # last  END_SYSEX (0xF7)
    def test_send_sysex_message(self):
        # 0x79 is queryFirmware, but that doesn't matter for now
        self.board.send_sysex(0x79, [1, 2, 3])
        sysex = (0xF0, 0x79, 1, 2, 3, 0xF7)
        self.assert_serial(*sysex)

    def test_send_sysex_to_big_data(self):
        self.assertRaises(ValueError, self.board.send_sysex, 0x79, [256, 1])

    def test_receive_sysex_message(self):
        sysex = bytearray([0xF0, 0x79, 2, 1, ord('a'), 0, ord('b'),
            0, ord('c'), 0, 0xF7])
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
        self.board.analog_pins[4].mode = pyfirmata.ANALOG
        self.board.sp.clear()
        # Crap
        self.board.sp.write([i for i in range(10)])
        # This should set analog port 4 to 1
        self.board.sp.write([pyfirmata.ANALOG_MESSAGE + 4, 127, 7])
        # Crap
        self.board.sp.write([10-i for i in range(10)])
        while len(self.board.sp):
            self.board.iterate()
        self.assertEqual(self.board.analog_pins[4].read(), 1.0)

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
        data = chain([0xF0, 0x70, 2], to_two_bytes(544),
            to_two_bytes(2400), [0xF7, 0xE0 + 2, 0, 0])
        self.assert_serial(*list(data))

    def test_servo_config_min_max_pulse(self):
        self.board.servo_config(2, 600, 2000)
        data = chain([0xF0, 0x70, 2], to_two_bytes(600),
            to_two_bytes(2000), [0xF7, 0xE0 + 2, 0, 0])
        self.assert_serial(*data)

    def test_servo_config_min_max_pulse_angle(self):
        self.board.servo_config(2, 600, 2000, angle=90)
        data = chain([0xF0, 0x70, 2], to_two_bytes(600),
            to_two_bytes(2000), [0xF7])
        angle_set = [0xE0 + 2, 90 % 128,
            90 >> 7] # Angle set happens through analog message
        data = list(data) + angle_set
        self.assert_serial(*data)

    def test_servo_config_invalid_pin(self):
        self.assertRaises(IOError, self.board.servo_config, 1)

    def test_set_mode_servo(self):
        # The underlying mechanism for setting the servo mode has changed.
        # Old: using Pin._set_mode to set to SERVO also executed the 
        # `self.board.servo_config(self, pin_number)` command.
        # This has the effect that whenever a servo mode was assigned, the 
        # servo goes to a specified angle (0 deg). This is not always the 
        # desired behavior (think about a servo-controlled 360deg rotor in a 
        # machine that needs to keep its previous position). 
        # Therefore, in pyfirmata, the `set_mode` and `servo_config` have
        # been discoupled. 
        #
        # Test is modified so that only the mode change is tested.
        servo_pin = self.board.pins[2]
        servo_pin.mode = pyfirmata.SERVO
        data = [0xF4, 0x02, 0x04]
        # this is the old `servo_config` command that was sent, is not used now
        # data = chain([0xF0, 0x70, 2], to_two_bytes(544),
        # to_two_bytes(2400), [0xF7, 0xE0 + 2, 0, 0])
        self.assert_serial(*data)


class TestBoardLayout(BoardBaseTest):

    def test_layout_arduino(self):
        self.assertEqual(len(BOARDS['arduino']['digital']), len(self.board.pins))
        self.assertEqual(len(BOARDS['arduino']['analog']), len(self.board.analog_pins))

    def test_layout_arduino_mega(self):
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        mega = pyfirmata.Board('ArduinoMega', BOARDS['arduino_mega'])
        self.assertEqual(len(BOARDS['arduino_mega']['digital']), len(mega.pins))
        self.assertEqual(len(BOARDS['arduino_mega']['analog']), len(mega.analog_pins))
        mega.exit()

    def test_pwm_layout(self):
        # For some reason, the board that is used in this method is the
        # Arduino Mega. As the Mega has different PWM's, things do not match
        # anymore
        pins = []
        for pin in self.board.pins:
            if self.board.pins[pin].pwm_capable:
                self.board.pins[pin].mode = pyfirmata.PWM
                pins.append(pin)
        for pin in pins:
            self.assertEqual(self.board.pins[pin].mode, pyfirmata.PWM)
            self.assertTrue(self.board.pins[pin].pin_number in BOARDS['arduino_mega']['pwm'])
        self.assertTrue(len(pins) == len(BOARDS['arduino']['pwm']))

    def test_get_pin_digital(self):
        pin = self.board.get_pin('d:13:o')
        self.assertEqual(pin.pin_number, 13)
        self.assertEqual(pin.mode, pyfirmata.OUTPUT)
        self.assertEqual(pin.get_port(), 1)
        self.assertEqual(self.board.ports[pin.get_port()].reporting, False)
        # test that the correct bytes have been sent to Firmata.
        # The first command sent is SET_PIN_MODE, should be: 0xF4, 0xD, 0x01
        self.assertEqual(list(self.board.sp), [0xF4, 13, 1])


    def test_get_pin_analog(self):
        pin = self.board.get_pin('a:5:i')
        self.assertEqual(pin.pin_number, 19)    # works for regular Arduino. A5==D19
        self.assertEqual(pin.reporting, True)
        self.assertEqual(pin.value, None)
        # test that the correct bytes have been sent to Firmata.
        # The first command sent is SET_PIN_MODE, should be: 0xF4, 0x13, 0x02
        # The second command sent is REPORT_ANALOG, should be: 0xC0 + 5, 0x01
        self.assertEqual(list(self.board.sp), [0xF4, 0x13, 0x02, 0xC0 + 5, 0x01])

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
        self.board._handle_digital_message(pin.get_port(),
            mask % 128, mask >> 7)
        self.assertEqual(pin.value, True)

    def test_handle_digital_inputs(self):
        """
        Test if digital inputs are correctly updated.
        """
        for i in range(8, 16): # pins of port 1
            if not bool(i%2) and i != 14: # all even pins
                self.board.pins[i].mode = pyfirmata.INPUT
                self.assertEqual(self.board.pins[i].value, None)
            else:
                # set to OUTPUT, as default Arduino digital pin is set to INPUT
                # the value should be None, as it cannot be altered
                self.board.pins[i].mode = pyfirmata.OUTPUT
        mask = 0
        # Set the mask high for the first 4 pins
        for i in range(4):
            mask |= 1 << i
        self.board._handle_digital_message(1, mask % 128, mask >> 7)
        self.assertEqual(self.board.pins[8].value, True)
        self.assertEqual(self.board.pins[9].value, None)
        self.assertEqual(self.board.pins[10].value, True)
        self.assertEqual(self.board.pins[11].value, None)
        self.assertEqual(self.board.pins[12].value, False)
        self.assertEqual(self.board.pins[13].value, None)

from pyfirmata.util import (to_two_bytes, from_two_bytes, two_byte_iter_to_str,
    str_to_two_byte_iter, break_to_bytes)


class UtilTests(unittest.TestCase):
    
    def test_to_two_bytes(self):
        for i in range(32768):
            val = to_two_bytes(i)
            self.assertEqual(len(val), 2)

        self.assertEqual(to_two_bytes(32767), bytearray(b'\x7f\xff'))
        self.assertRaises(ValueError, to_two_bytes, 32768)

    def test_from_two_bytes(self):
        for i in range(32766, 32768):
            val = to_two_bytes(i)
            ret = from_two_bytes(val)
            self.assertEqual(ret, i)

        self.assertEqual(from_two_bytes(('\xff', '\xff')), 32767)
        self.assertEqual(from_two_bytes(('\x7f', '\xff')), 32767)

    def test_two_byte_iter_to_str(self):
        string, s = 'StandardFirmata', []
        for i in string:
          s.append(i)
          s.append('\x00')
        self.assertEqual(two_byte_iter_to_str(s), 'StandardFirmata')

    def test_str_to_two_byte_iter(self):
        string, itr = 'StandardFirmata', bytearray()
        for i in string:
          itr.append(ord(i))
          itr.append(0)
        self.assertEqual(itr, str_to_two_byte_iter(string))

    def test_break_to_bytes(self):
        self.assertEqual(break_to_bytes(200), (200,))
        self.assertEqual(break_to_bytes(800), (200, 4))
        self.assertEqual(break_to_bytes(802), (2, 2, 200))


board_messages = unittest.TestLoader().loadTestsFromTestCase(TestBoardMessages)
board_layout = unittest.TestLoader().loadTestsFromTestCase(TestBoardLayout)
regression = unittest.TestLoader().loadTestsFromTestCase(RegressionTests)
util = unittest.TestLoader().loadTestsFromTestCase(UtilTests)
default = unittest.TestSuite([board_messages, board_layout, regression, util])
mockup_suite = unittest.TestLoader().loadTestsFromTestCase(TestMockupBoardLayout)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-m", "--mockup", dest="mockup", action="store_true",
        help="Also run the mockup tests")
    options, args = parser.parse_args()
    if not options.mockup:
        print("Running normal suite. Also consider running the mockup (-m, --mockup) suite")
        unittest.TextTestRunner(verbosity=3).run(default)
    if options.mockup:
        print("Running the mockup test suite")
        unittest.TextTestRunner(verbosity=2).run(mockup_suite)
