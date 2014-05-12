import unittest

from mockup import MockupSerial
from pyfirmata.util import *

class TestMockupSerial(unittest.TestCase):
    def test_mockup_serial(self):
        s = MockupSerial('someport', 4800)
        self.assertEqual(s.read(), '')
        s.write(chr(100))
        s.write('blaat')
        s.write(100000)
        self.assertEqual(s.read(2), ['d', 'blaat'])
        self.assertEqual(s.read(), 100000)
        self.assertEqual(s.read(), '')
        self.assertEqual(s.read(2), ['', ''])
        s.close()
        # TODO: Test .clear. pySerial does not have clear

class UtilTest(unittest.TestCase):

    def test_to_two_bytes(self):
        for i in range(32768):
            val = to_two_bytes(i)
            self.assertEqual(len(val), 2)

        self.assertEqual(to_two_bytes(32767), ('\x7f', '\xff'))
        with self.assertRaises(ValueError):
            to_two_bytes(32768)

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
            s.append(0x00)
        self.assertEqual(two_byte_iter_to_str(s), 'StandardFirmata')

        string, s = 'StandardFirmata', []
        for i in string:
            s.append(ord(i))
            s.append(ord('\x00'))
        self.assertEqual(two_byte_iter_to_str(s), 'StandardFirmata')

    def test_str_to_two_byte_iter(self):
        string, iter = 'StandardFirmata', []
        for i in string:
            iter.append(i)
            iter.append('\x00')
        self.assertEqual(iter, str_to_two_byte_iter(string))

    def test_break_to_bytes(self):
        self.assertEqual(break_to_bytes(200), (200,))
        self.assertEqual(break_to_bytes(800), (200, 4))
        self.assertEqual(break_to_bytes(802), (2, 2, 200))

if __name__ == '__main__':
    unittest.main()
