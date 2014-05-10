import unittest
import doctest
from optparse import OptionParser

import pyfirmata
from  test import *


# Default
class DefaultRegresstion(BoardBaseTest, RegressionTests):
    pass

class DefaultLayout(BoardBaseTest, TestBoardLayout):
    pass

class DefaultMessages(BoardBaseTest, TestBoardLayout):
    pass

# Mockup
class MockupRegresstion(MockupBoard, RegressionTests):
    pass

class MockupLayout(MockupBoard, TestBoardLayout):
    pass

class MockupMessages(MockupBoard, TestBoardLayout):
    pass

# Arduino
class ArduinoRegresstion(ArduinoDetection, RegressionTests):
    pass

class ArduinoLayout(ArduinoDetection, TestBoardLayout):
    pass

class ArduinoMessages(ArduinoDetection, TestBoardLayout):
    pass


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m", "--mockup", dest="mockup", action="store_true",
        help="Also run the mockup tests")
    parser.add_option("-a", "--arduino", dest="arduino", action="store_true",
        help="Run board dependent tests. Needs an Arduino connected on USB. \
                This Arduino must be running a Firmata >2.3 Sketch")
    options, args = parser.parse_args()

    test_list = []
    loader = unittest.TestLoader()

    if options.arduino:
        print "Running the Arduino dependent test suite"
        test_list += [ArduinoLayout, ArduinoMessages, ArduinoRegresstion]

    elif options.mockup:
        print "Running the mockup test suite"
        test_list += [MockupLayout, MockupMessages, MockupRegresstion]
    else:
        print "Running normal suite. Also consider running the mockup (-m, --mockup) suite"
        test_list += [DefaultLayout, DefaultMessages, DefaultRegresstion]

    suites_list = []
    for test_class in test_list:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    test_suite = unittest.TestSuite(suites_list)
    unittest.TextTestRunner(verbosity=3).run(test_suite)
