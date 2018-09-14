from collections import deque
import pyfirmata2


class MockupSerial(deque):
    """
    A Mockup object for python's Serial. Functions as a fifo-stack. Push to
    it with ``write``, read from it with ``read``.
    """

    def __init__(self, port, baudrate, timeout=0.02):
        self.port = port or 'somewhere'

    def read(self, count=1):
        if count > 1:
            val = []
            for i in range(count):
                try:
                    val.append(self.popleft())
                except IndexError:
                    break
        else:
            try:
                val = self.popleft()
            except IndexError:
                val = bytearray()

        val = [val] if not hasattr(val, '__iter__') else val
        return bytearray(val)

    def write(self, value):
        """
        Appends bytes flat to the deque. So iterables will be unpacked.
        """
        if hasattr(value, '__iter__'):
            bytearray(value)
            self.extend(value)
        else:
            bytearray([value])
            self.append(value)

    def close(self):
        self.clear()

    def inWaiting(self):
        return len(self)


class MockupBoard(pyfirmata2.Board):

    def __init__(self, port, layout, values_dict={}):
        self.sp = MockupSerial(port, 57600)
        self.setup_layout(layout)
        self.values_dict = values_dict
        self.id = 1
        self.samplerThread = Iterator(self)

    def reset_taken(self):
        for key in self.taken['analog']:
            self.taken['analog'][key] = False
        for key in self.taken['digital']:
            self.taken['digital'][key] = False

    def update_values_dict(self):
        for port in self.digital_ports:
            port.values_dict = self.values_dict
            port.update_values_dict()
        for pin in self.analog:
            pin.values_dict = self.values_dict


class MockupPort(pyfirmata2.Port):
    def __init__(self, board, port_number):
        self.board = board
        self.port_number = port_number
        self.reporting = False

        self.pins = []
        for i in range(8):
            pin_nr = i + self.port_number * 8
            self.pins.append(MockupPin(self.board, pin_nr, type=pyfirmata2.DIGITAL, port=self))

    def update_values_dict(self):
        for pin in self.pins:
            pin.values_dict = self.values_dict


class MockupPin(pyfirmata2.Pin):
    def __init__(self, *args, **kwargs):
        self.values_dict = kwargs.get('values_dict', {})
        try:
            del kwargs['values_dict']
        except KeyError:
            pass
        super(MockupPin, self).__init__(*args, **kwargs)

    def read(self):
        if self.value is None:
            try:
                type = self.port and 'd' or 'a'
                return self.values_dict[type][self.pin_number]
            except KeyError:
                return None
        else:
            return self.value

    def get_in_output(self):
        if not self.port and not self.mode:  # analog input
            return 'i'
        else:
            return 'o'

    def set_active(self, active):
        self.is_active = active

    def get_active(self):
        return self.is_active

    def write(self, value):
        if self.mode == pyfirmata2.UNAVAILABLE:
            raise IOError("Cannot read from pin {0}".format(self.pin_number))
        if self.mode == pyfirmata2.INPUT:
            raise IOError("{0} pin {1} is not an output"
                          .format(self.port and "Digital" or "Analog", self.get_pin_number()))
        if not self.port:
            raise AttributeError("AnalogPin instance has no attribute 'write'")
        # if value != self.read():
        self.value = value


class Iterator(object):
    def __init__(self, *args, **kwargs):
        self.running = False

    def start(self):
        pass

    def stop(self):
        pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()
    # TODO make these unittests as this doesn't work due to relative imports
