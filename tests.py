from __future__ import division, unicode_literals

import unittest
from itertools import chain

import serial

import pyfirmata
from pyfirmata import mockup
from pyfirmata.boards import BOARDS
from pyfirmata.util import (
    break_to_bytes, from_two_bytes, str_to_two_byte_iter, to_two_bytes, two_byte_iter_to_str
)


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
        self.board = pyfirmata.Board('', BOARDS['arduino'])
        self.board._stored_data = []
        # FIXME How can it be that a fresh instance sometimes still contains data?


class TestBoardMessages(BoardBaseTest):
    # TODO Test layout of Board Mega
    def assert_serial(self, *incoming_bytes):
        serial_msg = bytearray()
        res = self.board.sp.read()
        while res:
            serial_msg += res
            res = self.board.sp.read()
        self.assertEqual(bytearray(incoming_bytes), serial_msg)

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
        self.board.digital[5]._mode = 0  # Set it to input
        # Create the mask
        mask = 0
        mask |= 1 << 5  # set the bit for pin 5 to to 1
        self.assertEqual(self.board.digital[5].read(), None)
        self.board._handle_digital_message(0, mask % 128, mask >> 7)
        self.assertEqual(self.board.digital[5].read(), True)

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
        self.assertEqual(self.board.analog[4].read(), None)
        self.assertEqual(self.board.analog[4].reporting, False)
        # Should do nothing as the pin isn't set to report
        self.board.sp.write([pyfirmata.ANALOG_MESSAGE + 4, 127, 7])
        self.board.iterate()
        self.assertEqual(self.board.analog[4].read(), None)
        self.board.analog[4].enable_reporting()
        self.board.sp.clear()
        # This should set analog port 4 to 1
        self.board.sp.write([pyfirmata.ANALOG_MESSAGE + 4, 127, 7])
        self.board.iterate()
        self.assertEqual(self.board.analog[4].read(), 1.0)
        self.board._stored_data = []

    def test_handle_capability_response(self):
        """
        Capability Response codes:

        # INPUT:  0, 1
        # OUTPUT: 1, 1
        # ANALOG: 2, 10
        # PWM:    3, 8
        # SERV0:  4, 14
        # I2C:    6, 1

        Arduino's Example: (ATMega328P-PU)

        (127,
         127,
         0, 1, 1, 1, 4, 14, 127,
         0, 1, 1, 1, 3, 8, 4, 14, 127,
         0, 1, 1, 1, 4, 14, 127,
         0, 1, 1, 1, 3, 8, 4, 14, 127,
         0, 1, 1, 1, 3, 8, 4, 14, 127,
         0, 1, 1, 1, 4, 14, 127,
         0, 1, 1, 1, 4, 14, 127,
         0, 1, 1, 1, 3, 8, 4, 14, 127,
         0, 1, 1, 1, 3, 8, 4, 14, 127,
         0, 1, 1, 1, 3, 8, 4, 14, 127,
         0, 1, 1, 1, 4, 14, 127,
         0, 1, 1, 1, 4, 14, 127,
         0, 1, 1, 1, 2, 10, 127,
         0, 1, 1, 1, 2, 10, 127,
         0, 1, 1, 1, 2, 10, 127,
         0, 1, 1, 1, 2, 10, 127,
         0, 1, 1, 1, 2, 10, 6, 1, 127,
         0, 1, 1, 1, 2, 10, 6, 1, 127)
         """

        test_layout = {
            'digital': (0, 1, 2),
            'analog': (0, 1),
            'pwm': (1, 2),
            'servo': (0, 1, 2),
            # 'i2c': (2),  # TODO 2.3 specs
            'disabled': (0,),
        }

        # Eg: (127)
        unavailible_pin = [
            0x7F,  # END_SYSEX (Pin delimiter)
        ]

        # Eg: (0, 1, 1, 1, 3, 8, 4, 14, 127)
        digital_pin = [
            0x00,  # INPUT
            0x01,
            0x01,  # OUTPUT
            0x01,
            0x03,  # PWM
            0x08,
            0x7F,  # END_SYSEX (Pin delimiter)
        ]

        # Eg. (0, 1, 1, 1, 4, 14, 127)
        analog_pin = [
            0x00,  # INPUT
            0x01,
            0x01,  # OUTPUT
            0x01,
            0x02,  # ANALOG
            0x0A,
            0x06,  # I2C
            0x01,
            0x7F,  # END_SYSEX (Pin delimiter)
        ]

        data_arduino = list(
            [0x6C]  # CAPABILITY_RESPONSE
            + unavailible_pin
            + digital_pin * 2
            + analog_pin * 2
        )

        self.board._handle_report_capability_response(*data_arduino)
        for key in test_layout.keys():
            self.assertEqual(self.board._layout[key], test_layout[key])

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # digital I/O message   0x90   port       LSB(bits 0-6)         MSB(bits 7-13)
    def test_incoming_digital_message(self):
        # A digital message sets the value for a whole port. We will set pin
        # 9 (on port 1) to 1 to test if this is working.
        self.board.digital[9].mode = pyfirmata.INPUT
        self.board.sp.clear()  # clear mode sent over the wire.
        # Create the mask
        mask = 0
        mask |= 1 << (9 - 8)  # set the bit for pin 9 to to 1
        self.assertEqual(self.board.digital[9].read(), None)
        self.board.sp.write([pyfirmata.DIGITAL_MESSAGE + 1, mask % 128, mask >> 7])
        self.board.iterate()
        self.assertEqual(self.board.digital[9].read(), True)

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
        self.board.analog[1].enable_reporting()
        self.assert_serial(0xC0 + 1, 1)
        self.assertTrue(self.board.analog[1].reporting)
        self.board.analog[1].disable_reporting()
        self.assert_serial(0xC0 + 1, 0)
        self.assertFalse(self.board.analog[1].reporting)

    # type                command  channel    first byte            second byte
    # ---------------------------------------------------------------------------
    # report digital port   0xD0   port       disable/enable(0/1)   - n/a -
    def test_report_digital(self):
        # This should enable reporting of whole port 1
        self.board.digital[8]._mode = pyfirmata.INPUT  # Outputs can't report
        self.board.digital[8].enable_reporting()
        self.assert_serial(0xD0 + 1, 1)
        self.assertTrue(self.board.digital_ports[1].reporting)
        self.board.digital[8].disable_reporting()
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

    def test_send_sysex_string(self):
        self.board.send_sysex(0x79, bytearray("test", 'ascii'))
        sysex = [0xF0, 0x79]
        sysex.extend(bytearray('test', 'ascii'))
        sysex.append(0xF7)
        self.assert_serial(*sysex)

    def test_send_sysex_too_big_data(self):
        self.assertRaises(ValueError, self.board.send_sysex, 0x79, [256, 1])

    def test_receive_sysex_message(self):
        sysex = bytearray([0xF0, 0x79, 2, 1, ord('a'), 0, ord('b'), 0, ord('c'), 0, 0xF7])
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
        self.board.sp.write([i for i in range(10)])
        # This should set analog port 4 to 1
        self.board.sp.write([pyfirmata.ANALOG_MESSAGE + 4, 127, 7])
        # Crap
        self.board.sp.write([10 - i for i in range(10)])
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
        data = chain([0xF0, 0x70, 2],
                     to_two_bytes(544),
                     to_two_bytes(2400),
                     [0xF7, 0xE0 + 2, 0, 0])
        self.assert_serial(*list(data))

    def test_servo_config_min_max_pulse(self):
        self.board.servo_config(2, 600, 2000)
        data = chain([0xF0, 0x70, 2],
                     to_two_bytes(600),
                     to_two_bytes(2000),
                     [0xF7, 0xE0 + 2, 0, 0])
        self.assert_serial(*data)

    def test_servo_config_min_max_pulse_angle(self):
        self.board.servo_config(2, 600, 2000, angle=90)
        data = chain([0xF0, 0x70, 2], to_two_bytes(600), to_two_bytes(2000), [0xF7])
        angle_set = [0xE0 + 2, 90 % 128, 90 >> 7]  # Angle set happens through analog message
        data = list(data) + angle_set
        self.assert_serial(*data)

    def test_servo_config_invalid_pin(self):
        self.assertRaises(IOError, self.board.servo_config, 1)

    def test_set_mode_servo(self):
        p = self.board.digital[2]
        p.mode = pyfirmata.SERVO
        data = chain([0xF0, 0x70, 2],
                     to_two_bytes(544),
                     to_two_bytes(2400),
                     [0xF7, 0xE0 + 2, 0, 0])
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


class TestMockupSerial(unittest.TestCase):

    def setUp(self):
        self.s = mockup.MockupSerial('someport', 4800)

    def test_only_bytes(self):
        self.s.write(0xA0)
        self.s.write(100)
        self.assertRaises(TypeError, self.s.write, 'blaat')

    def test_write_read(self):
        self.s.write(0xA1)
        self.s.write([1, 3, 5])
        self.assertEqual(self.s.read(2), bytearray([0xA1, 0x01]))
        self.assertEqual(len(self.s), 2)
        self.assertEqual(self.s.read(), bytearray([3]))
        self.assertEqual(self.s.read(), bytearray([5]))
        self.assertEqual(len(self.s), 0)
        self.assertEqual(self.s.read(), bytearray())
        self.assertEqual(self.s.read(2), bytearray())

    def test_none(self):
        self.assertEqual(self.s.read(), bytearray())


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
        mask |= 1 << 0  # set pin 0 high
        self.board._handle_digital_message(pin.port.port_number, mask % 128, mask >> 7)
        self.assertEqual(pin.value, True)

    def test_handle_digital_inputs(self):
        """
        Test if digital inputs are correctly updated.
        """
        for i in range(8, 16):  # pins of port 1
            if not bool(i % 2) and i != 14:  # all even pins
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

    def test_proper_exit_conditions(self):
        """
        Test that the exit method works properly if we didn't make it all
        the way through `setup_layout`.
        """
        del self.board.digital
        try:
            self.board.exit()
        except AttributeError:
            self.fail("exit() raised an AttributeError unexpectedly!")


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
