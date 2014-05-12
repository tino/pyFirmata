import unittest
from optparse import OptionParser

import pyfirmata
from test import *


# Default
class DefaultRegresstion(BoardBaseTest, RegressionTests):
    pass

class DefaultLayout(BoardBaseTest, TestBoardLayout):
    pass

class DefaultMessages(BoardBaseTest, TestBoardMessages):
    pass

class DefaultHandlers(BoardBaseTest, TestBoardHandlers):
    pass

# Mockup
class MockupRegresstion(MockupBoard, RegressionTests):
    pass

class MockupLayout(MockupBoard, TestBoardLayout):
    pass

class MockupMessages(MockupBoard, TestBoardMessages):
    pass

class MockupHandlers(MockupBoard, TestBoardHandlers):
    pass

# Arduino
class ArduinoRegresstion(ArduinoDetection, RegressionTests):
    pass

class ArduinoLayout(ArduinoDetection, TestBoardLayout):

    @unittest.skip('Makes no sense, since we are detecting the laytout')
    def test_layout_arduino(self):
        pass

    @unittest.skip('Makes no sense, since we are detecting the laytout')
    def test_layout_arduino_mega(self):
        pass

#class ArduinoMessages(ArduinoDetection, TestBoardMessages):
#    pass

class ArduinoHandlers(ArduinoDetection, TestBoardHandlers):
    pass

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m", "--mockup", dest="mockup", action="store_true",
        help="Also run the mockup tests")
    parser.add_option("-a", "--arduino", dest="arduino", action="store_true",
        help="Run board dependent tests. Needs an Arduino connected on USB. \
                This Arduino must be running a Firmata >2.3 Sketch")
    options, args = parser.parse_args()

    test_list = [UtilTest, TestMockupSerial]
    loader = unittest.TestLoader()

    if options.arduino:
        print "Running the Arduino dependent test suite"
        test_list += [
            ArduinoLayout,
            #ArduinoMessages,
            ArduinoRegresstion,
            ArduinoHandlers,
        ]

    elif options.mockup:
        print "Running the mockup test suite"
        test_list += [
                MockupLayout,
                MockupMessages,
                MockupRegresstion,
                MockupHandlers
        ]
    else:
        print "Running normal suite. Also consider running the mockup (-m, --mockup) suite"
        test_list += [
            DefaultLayout,
            DefaultMessages,
            DefaultRegresstion,
            DefaultHandlers,
        ]

    suites_list = []
    for test_class in test_list:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    test_suite = unittest.TestSuite(suites_list)
    unittest.TextTestRunner(verbosity=3).run(test_suite)
