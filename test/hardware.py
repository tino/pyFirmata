import abc
import time

import pyfirmata
from pyfirmata import OUTPUT, INPUT, SERVO

class TestHardwareBoard(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self):
        pass

    @abc.abstractmethod
    def tearDown(self):
        pass

    def test_analog_read_reporting_enabled(self):
        self.it.start()
        pin_a4 = self.board.analog[4]
        pin_a4.enable_reporting()
        time.sleep(0.1)
        # There is a 200 ohms resistor connected to this pin
        a4value = pin_a4.read()
        self.assertNotEqual(a4value, None)

    def test_analog_read_not_reporting(self):
        self.it.start()
        pin_a4 = self.board.analog[4]
        time.sleep(0.1)
        self.assertEqual(pin_a4.read(), None)

    def test_analog_pin_numbers(self):
        self.it.start()
        pin_gnd = self.board.analog[3]
        pin_200ohm = self.board.analog[4]
        pin_ldr = self.board.analog[5]
        my_pins = [pin_gnd, pin_200ohm, pin_ldr]
        for pin in my_pins:
            pin.enable_reporting()
        time.sleep(0.1)

        # This pin is connected to the GND
        self.assertEqual(pin_gnd.read(), 0.0)
        # There is a 200 ohms resistor connected to this pin
        self.assertGreater(pin_200ohm.read(), 0.980)
        self.assertLess(pin_200ohm.read(), 0.990)
        # There is a LDR connected to this pin
        self.assertGreater(pin_ldr.read(), 0.0)
        self.assertLess(pin_ldr.read(), 1.0)

    def test_digital_read_reporting_enabled(self):
        self.it.start()
        pin_d2 = self.board.digital[2]
        pin_d2.mode = INPUT
        pin_d2.enable_reporting()
        time.sleep(0.1)
        d2value = pin_d2.read()
        self.assertNotEqual(d2value, None)
        # This pin is connected to the VDD
        self.assertEqual(d2value, True)

    def test_digital_read_not_reporting(self):
        self.it.start()
        # enable_reporting required just for analog pins
        pin_d2 = self.board.digital[2]
        pin_d2.mode = INPUT
        time.sleep(0.1)
        self.assertEqual(pin_d2.read(), True)

    def test_digital_write(self):
        seven_segments = [
            self.board.digital[9],
            self.board.digital[5],
            self.board.digital[6],
            self.board.digital[7],
            self.board.digital[8],
            self.board.digital[10],
            self.board.digital[11],
            self.board.digital[12],
        ]
        for pin in seven_segments:
            pin.mode = OUTPUT

        # Look the the LEDs
        for pin in seven_segments:
            pin.write(1)
            time.sleep(0.1)
            pin.write(0)

    def test_firmata_version(self):
        self.it.start()
        version = self.board.get_firmata_version()
        self.assertEqual(version, self.FIRMWARE_VERSION)


    def test_pwm_pins(self):
        pwm_pins = [p for p in self.board.digital if p.PWM_CAPABLE]
        pins_n = [p.pin_number for p in pwm_pins]
        self.assertEqual(pins_n, [3, 5, 6, 9, 10, 11])
        for pin in pwm_pins:
            pin.mode = pyfirmata.PWM

        # Look the the LEDs
        for frequency in range(0, 1000, 10) + range(0, 1000, 10)[::-1]:
            for p in pwm_pins:
                p.write(float(frequency)/1000.0)
            time.sleep(0.01)

    def test_servo(self):
        # Sweep Example
        pin_d3 = self.board.digital[3]
        pin_d3.mode = SERVO

        for pos in xrange(180):
            pin_d3.write(pos)
            time.sleep(0.015)

        for pos in xrange(180, 0, -1):
            pin_d3.write(pos)
            time.sleep(0.015)
