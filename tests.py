import unittest
from optparse import OptionParser

import pyfirmata
from test import *

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
