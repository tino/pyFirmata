import abc

import pyfirmata


class TestHardwareBoard(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self):
        pass

    @abc.abstractmethod
    def tearDown(self):
        pass

    def test_analog_not_reporting(self):
        pass

    def test_analog_reporting_enabled(self):
        pass

    def test_report_analog(self):
        pass

    def test_report_digital(self):
        pass

    def test_incoming_digital_message(self):
        pass

    def test_incoming_report_version(self):
        pass

    def test_incoming_report_firmware(self):
        pass
