import abc
from itertools import chain

import pyfirmata
from pyfirmata.util import to_two_bytes, str_to_two_byte_iter


class TestBoardHandlers(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self):
        pass

    @abc.abstractmethod
    def tearDown(self):
        pass

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

    def test_handle_capability_response(self):
        test_layout = {
            'digital': (0, 1, 2),
            'analog': (0, 1),
            'pwm': (1, 2),
            #'servo': (2), # TODO 2.2 specs
            #'i2c': (2), # TODO 2.3 specs
            'disabled': (0,),
        }

        # Eg: (127)
        unavailible_pin = [
            0x7F, # END_SYSEX (Pin delimiter)
        ]

        # Eg: (0, 1, 1, 1, 3, 8, 4, 14, 127)
        digital_pin = [
                0x00, # INPUT
                0x01,
                0x01, # OUTPUT
                0x01,
                0x03, # PWM
                0x08,
                0x7F, # END_SYSEX (Pin delimiter)
        ]

        # Eg. (0, 1, 1, 1, 4, 14, 127)
        analog_pin = [
                0x00, # INPUT
                0x01,
                0x01, # OUTPUT
                0x01,
                0x02, # ANALOG
                0x0A,
                0x06, # I2C
                0x01,
                0x7F, # END_SYSEX (Pin delimiter)
        ]

        data_arduino = list(
            [0x6C] # CAPABILITY_RESPONSE
            + unavailible_pin
            + digital_pin * 2
            + analog_pin * 2
        )

        self.board._handle_report_capability_response(*data_arduino)
        for key in test_layout.keys():
            self.assertEqual(self.board._layout[key], test_layout[key])

    def test_handle_pin_state_response(self):
        # 2.2 specs
        pass


# Messages todo left:

# type                command  channel    first byte            second byte
# ---------------------------------------------------------------------------
# set pin mode(I/O)     0xF4              pin # (0-127)         pin state(0=in)
# system reset          0xFF

class TestBoardMessages(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self):
        pass

    # TODO Test layout of Board Mega
    def assert_serial(self, *list_of_chrs):
        res = self.board.sp.read()
        serial_msg = res
        while res:
            res = self.board.sp.read()
            serial_msg += res
        self.assertEqual(''.join(list(list_of_chrs)), serial_msg)

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

    def test_send_sysex_string(self):
        self.board.send_sysex(0x79, ["test"])
        sysex = (chr(0xF0), chr(0x79), 't', 'e', 's', 't', chr(0xF7))
        self.assert_serial(*sysex)

    def test_send_sysex_too_big_data(self):
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

