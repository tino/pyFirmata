import abc
import unittest

import pyfirmata

class RegressionTests(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def setUp(self):
        pass

    @abc.abstractmethod
    def tearDown(self):
        pass

    def test_correct_digital_input_first_pin_issue_9(self):
        """
        The first pin on the port would always be low, even if the mask said
        it to be high.
        """
        pin = self.board.get_pin('d:8:i')
        mask = 0
        mask |= 1 << 0 # set pin 0 high
        self.board._handle_digital_message(pin.port.port_number,
            mask % 128, mask >> 7)
        self.assertEqual(pin.value, True)

    def test_handle_digital_inputs(self):
        """
        Test if digital inputs are correctly updated.
        """
        for i in range(8, 16): # pins of port 1
            if not bool(i%2) and i != 14: # all even pins
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

