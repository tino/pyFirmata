
class LED(object):
    """The LED component class"""

    def __init__(self, board, pin_number):
        self.pin_number = pin_number
        self.__pin = board.get_pin('d:%d:o' % self.pin_number)
        self.off()

    def on(self):
        self.__pin.write(1)

    def off(self):
        self.__pin.write(0)

    def toggle(self):
        self.__pin.write(1 - self.__pin.read())


class Servo(object):
    """The servo component class"""

    def __init__(self, board, pin_number, min_pulse=544, max_pulse=2400, angle=0):
        self.pin_number = pin_number
        self.__pin = board.get_pin('d:%d:o' % self.pin_number)
        board.servo_config(self.pin_number, min_pulse, max_pulse, angle)

    def set(self, angle):
        self.__pin.write(angle)


class LCD(object):
    """
    Only 4 bit mode supported
    """

    def __init__(self, board, data, rs, enable):
        # Data pins
        if len(data) != 4:
            raise RuntimeError, 'Invalid number of data pins, must be 4'

        self.__data = [board.get_pin('d:%d:o' % p) for p in map(int, data)]
        self.__rs = board.get_pin('d:%d:o' % int(rs))
        self.__enable = board.get_pin('d:%d:o' % int(enable))
        self.__setup()
 
    def __send_half_word(self, half_word):
        for pin, value in zip(self.__data, [half_word >> i & 0x01 for i in xrange(4)]):
            pin.write(value)

        self.__enable.write(1)
        self.__enable.write(0)

    def __send(self, word, mode):
        self.__rs.write(mode)

        self.__send_half_word(word >> 4 & 0xF)
        self.__send_half_word(word & 0xF)

    def __command(self, word):
        self.__send(word, 0)

    def __setup(self):
        self.__rs.write(0)
        self.__enable.write(0)

        # Reset and 4-bit
        self.__command(0x33)
        self.__command(0x32)

        # Function set: 4-bit, 1 line, 5x8 dots
        self.__command(0x28)
        # Display control: turn display on, cursor off, no blinking
        self.__command(0x0C)
        # Entry mode set: increment automatically, display shift, right shift
        self.__command(0x06)

        self.clear()

    def __write(self, word):
        self.__send(word, 1)

    def clear(self):
        self.__command(0x01)

    def home(self):
        self.__command(0x02)

    def write(self, chars):
        for char in chars:
            self.__write(ord(char))

    def set_cursor(self, col, row):
        offsets = [0x00, 0x40]
        self.__command(0x80 | (col + offsets[row]))

