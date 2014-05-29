from regression import RegressionTests
from layout import TestBoardLayout
from messages import TestBoardMessages, TestBoardHandlers
from boardbases import BoardBaseTest, ArduinoDetection, MockupBoard
from util import UtilTest, TestMockupSerial
from hardware import TestHardwareBoard

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

class ArduinoHardware(ArduinoDetection, TestHardwareBoard):
    pass
