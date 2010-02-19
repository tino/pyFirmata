import unittest
import serial
import time
from optparse import OptionParser

import pyfirmata
from pyfirmata import mockup

class TestLiveBoards(unittest.TestCase):
    """
    Test two live boards. On the 'transmitter' board:
    
    - connect 5v and analog port 0 directly
    - connect digital port 2 to the 'receiver' board's analog port 2 directly
    - connect digital port 5 to the 'receiver' board's analog port 5 directly
    - connect 3v to the 'receiver' board's analog port 1 directly
    
    On the 'receiver' board:
    
    - connect ground and analog port 0 directly
    
    ..note::
        This test can take quite a while, as it may take about 4 seconds each
        time the setUp function is called.
    """
    
    def setUp(self):
        self.boards = pyfirmata.Boards()
        assert len(self.boards) >= 2, "Only %d board(s) found. I need at least 2!" % len(boards)
        x, y = self.boards.values()[0], self.boards.values()[1]
        it1, it2 = pyfirmata.Iterator(x), pyfirmata.Iterator(y)
        it1.start(), it2.start()
        # give iterator time to iterate
        self.pass_time(0.1)
        x0, y0 = x.get_pin('a:0:i'), y.get_pin('a:0:i')
        self.pass_time(0.1)
        if x0.read() > 0.9 and y0.read() < 0.1: # x is transmitter
            self.transmitter = x
            self.receiver = y
        elif y0.read() > 0.9 and x0.read() < 0.1: # y is transmitter
            self.transmitter = x
            self.receiver = y
        else:
            self.fail("Could not complete setup. One, and only one of the \
                board's analog ports should be set high by connecting it to \
                its 5v output. That board will be considered the transmitter. \
                Values received: %f and %f" % (x0.read(), y0.read()))
        self.Ta0 = self.transmitter.analog[0] # already taken by line 36
        self.Ra1 = self.receiver.get_pin('a:1:i')
        self.Ra2 = self.receiver.get_pin('a:2:i')
        self.Ra5 = self.receiver.get_pin('a:5:i')
        self.Td2 = self.transmitter.get_pin('d:2:o')
        self.Td5 = self.transmitter.get_pin('d:5:p')
        self.Td13 = self.transmitter.get_pin('d:13:o')
        
    def iterate(self):
        self.transmitter.iterate()
        self.receiver.iterate()
        
    def pass_time(self, t):
        cont = time.time() + t
        while time.time() < cont:
            pass
            
    def test_led(self):
        self.Td13.write(1)
        print "Transmitters d13 should be high for 2 seconds..."
        self.pass_time(2)
        self.assertEqual(self.Td13.read(), 1)
        
    def test_high(self):
        self.pass_time(0.1)
        value = self.Ta0.read()
        self.failIf(value < 0.99, msg="Too low: %f" % value) # Connected to 5v, it should be almost 1
        value = self.Ra1.read()
        self.failUnless(0.65 < value < 0.69, msg="not getting 3v! (%f not between 0.65 and 0.69)" % value) # Connected to 3v
        
    def test_in_out(self):
        self.Td2.write(1)
        self.pass_time(0.1)
        value = self.Ra2.read()
        self.failIf(value < 0.99, msg="Not high enough: %f" % value)
        self.Td2.write(0)
        self.assert_(self.Td2.read() == 0)
        self.pass_time(0.1)
        value = self.Ra2.read()
        self.failIf(value > 0.01, msg="Too high: %f" % value)

    # pwm into analog doesn't work...
    def test_pwm(self):
        self.pass_time(0.5)
        # test high
        self.Td5.write(1.0)
        self.pass_time(1)
        value = self.Ra5.read()
        self.failUnless(0.99 < value < 1.0, msg="%f not between 0.99 and 1.0" % value)
        # test middle
        self.Td5.write(0.5)
        self.pass_time(0.5)
        value = self.Ra5.read()
        self.failUnless(0.49 < value < 0.51, msg="%f not between 0.49 and 0.51" % value)
        # test low
        self.Td5.write(0.1)
        self.pass_time(0.5)
        value = self.Ra5.read()
        self.failUnless(0.09 < value < 0.11, msg="%f not between 0.09 and 0.11" % value)
        
    def tearDown(self):
        self.boards.exit()

class TestBoard(unittest.TestCase):
    # TODO Test layout of Board Mega
    # TODO Test if messages are correct...
    
    def setUp(self):
        pyfirmata.pyfirmata.serial.Serial = mockup.MockupSerial
        self.board = pyfirmata.Board('test')
        # self.board.setup_layout(pyfirmata.BOARDS['normal'])

    def test_pwm_layout(self):
        pins = []
        for pin in self.board.digital:
            if pin.PWM_CAPABLE:
                pins.append(self.board.get_pin('d:%d:p' % pin.pin_number))
        for pin in pins:
            self.assertEqual(pin.mode, pyfirmata.PWM)
        
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
        
class TestMockupBoard(unittest.TestCase):
    
    def setUp(self):
        self.board = mockup.MockupBoard('test')
    
    def test_identifier(self):
        self.assertEqual(self.board.identifier, ord(chr(ID)))
    
    def test_pwm_layout(self):
        pins = []
        for pin_nr in self.board.layout['p']:
            pins.append(self.board.get_pin('d:%d:p' % pin_nr))
        for pin in pins:
            mode = pin.get_mode()
            self.assertEqual(mode, pyfirmata.DIGITAL_PWM)
        
    def test_get_pin_digital(self):
        pin = self.board.get_pin('d:13:o')
        self.assertEqual(pin.pin_number, 5)
        self.assertEqual(pin.mode, pyfirmata.DIGITAL_OUTPUT)
        self.assertEqual(pin.sp, self.board.sp)
        self.assertEqual(pin.port.port_number, 1)
        self.assertEqual(pin._get_board_pin_number(), 13)
        self.assertEqual(pin.port.get_active(), 1)
        
    def test_get_pin_analog(self):
        pin = self.board.get_pin('a:5:i')
        self.assertEqual(pin.pin_number, 5)
        self.assertEqual(pin.sp, self.board.sp)
        self.assertEqual(pin.get_active(), 1)
        self.assertEqual(pin.value, -1)
        
    def tearDown(self):
        self.board.exit()
        pyfirmata.serial.Serial = serial.Serial


suite = unittest.TestLoader().loadTestsFromTestCase(TestBoard)
live_suite = unittest.TestLoader().loadTestsFromTestCase(TestLiveBoards)
mockup_suite = unittest.TestLoader().loadTestsFromTestCase(TestMockupBoard)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-l", "--live", dest="live", action="store_true",
        help="Also run the live tests. Make sure the hardware is connected properly")
    parser.add_option("-m", "--mockup", dest="mockup", action="store_true",
        help="Also run the mockup tests")
    options, args = parser.parse_args()
    if not options.live and not options.mockup:
        print "Running normal suite. Also consider running the live (-l, --live) \
                and mockup (-m, --mockup) suites"
        unittest.TextTestRunner(verbosity=3).run(suite)
    if options.live:
        print "Running the live test suite"
        unittest.TextTestRunner(verbosity=2).run(live_suite)
    if options.mockup:
        print "Running the mockup test suite"
        unittest.TextTestRunner(verbosity=2).run(mockup_suite)
