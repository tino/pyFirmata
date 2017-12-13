"""Support module for I2C communication using Firmata sysexes."""

from .util import from_two_bytes, to_two_bytes, two_byte_iter_to_bytes

# extended command (sysex) codes:
I2C_REQUEST = 0x76          # send an I2C read/write request
I2C_REPLY = 0x77            # a reply to an I2C read request
I2C_CONFIG = 0x78           # config I2C settings such as delay times and power pins

# I2C modes:
I2C_WRITE = 0B00000000
I2C_READ = 0B00001000
I2C_READ_CONTINUOUSLY = 0B00010000
I2C_STOP_READING = 0B00011000


class I2C:
    """Class for communicating over I2C."""

    def __init__(self, board):
        """Init I2C connection class."""
        self.board = board
        self.board.add_cmd_handler(I2C_REQUEST, self._handle_i2c_request)
        self.board.add_cmd_handler(I2C_REPLY, self._handle_i2c_reply)
        self.started = False
        self.listeners = []

    def setup(self, delay=0):
        """Setup I2C connection."""
        self.board.send_sysex(I2C_CONFIG, to_two_bytes(delay))
        self.started = True

    def _construct_header(self, slave, mode, auto_restart=False):
        if slave > 1023:
            raise ValueError("I2C slave address cannot be bigger than 1023 (10-bit mode)")
        (lsb, msb) = to_two_bytes(slave)
        if slave > 127:
            msb |= 0B00100000
        if auto_restart:
            msb |= 0B01000000
        msb |= mode
        return [lsb, msb]

    def _read(self, slave, length, register, read_mode, auto_restart=False):
        if not self.started:
            self.setup()
        command = self._construct_header(slave, read_mode)
        if register is not None:
            command.extend(to_two_bytes(register))
        if length is not None:
            command.extend(to_two_bytes(length))
        self.board.send_sysex(I2C_REQUEST, command)

    def _get_listeners(self, slave, register):
        while len(self.listeners) <= slave:
            self.listeners.append([])
        while len(self.listeners[slave]) <= register:
            self.listeners[slave].append([])
        return self.listeners[slave][register]

    def set_listener(self, slave, register, listener):
        """Set listener function for given slave and register."""
        if register is None:
            register = 0
        listeners = self._get_listeners(slave, register)
        listeners.append(listener)

    def unset_listener(self, slave, register, listener=None):
        """Remove listener function for given slave and register."""
        if register is None:
            register = 0
        if listener is None:
            self.listeners[slave][register] = []
        else:
            self.listeners[slave][register].remove(listener)

    def send(self, slave, data, register=None):
        """Send data to the given slave."""
        if not self.started:
            self.setup()
        command = self._construct_header(slave, I2C_WRITE)
        if register is not None:
            command.extend(to_two_bytes(register))
        for d in data:
            command.extend(to_two_bytes(d))
        self.board.send_sysex(I2C_REQUEST, command)

    def _read_listener(self, data):
        self.readed_data = data

    def read(self, slave, length=None, register=None):
        """Read data of given length from given slave and register."""
        # Read once and than wait for result
        self.readed_data = None
        self.set_listener(slave, register, self._read_listener)
        self._read(slave, length, register, I2C_READ)
        while self.readed_data is None:
            pass
        self.unset_listener(slave, register, self._read_listener)
        return self.readed_data

    def start_reading(self, slave, length=None, register=None, auto_restart=False):
        """
         Start continuous reading of data given length from given slave and register.

        It reads every sampling interval. Listener should be set before this function.
        """
        self._read(slave, length, register, I2C_READ_CONTINUOUSLY, auto_restart)

    def stop_reading(self, slave):
        """Stop reading from given slave and register."""
        if not self.started:
            self.setup()
        command = self._construct_header(slave, I2C_STOP_READING)
        self.board.send_sysex(I2C_REQUEST, command)

    def _handle_i2c_request(self, slave_lsb, slave_msb, *data):
        print("I2C Request:", data)

    def _handle_i2c_reply(self, *data):
        slave = from_two_bytes(data[0:2])
        register = from_two_bytes(data[2:4])
        decoded_data = two_byte_iter_to_bytes(data[4:])
        for listener in self._get_listeners(slave, register):
            listener(decoded_data)
