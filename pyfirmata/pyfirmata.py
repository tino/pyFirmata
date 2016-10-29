from __future__ import division, unicode_literals

import inspect
import time

import serial

from .util import from_two_bytes, to_two_bytes, two_byte_iter_to_str, pin_list_to_board_dict, Iterator

# Message command bytes (0x80(128) to 0xFF(255)) - straight from Firmata.h
DIGITAL_MESSAGE = 0x90      # send data for a digital pin
ANALOG_MESSAGE = 0xE0       # send data for an analog pin (or PWM)
DIGITAL_PULSE = 0x91        # SysEx command to send a digital pulse

# PULSE_MESSAGE = 0xA0      # proposed pulseIn/Out msg (SysEx)
# SHIFTOUT_MESSAGE = 0xB0   # proposed shiftOut msg (SysEx)
REPORT_ANALOG = 0xC0        # enable analog input by pin #
REPORT_DIGITAL = 0xD0       # enable digital input by port pair
START_SYSEX = 0xF0          # start a MIDI SysEx msg
SET_PIN_MODE = 0xF4         # set a pin to INPUT/OUTPUT/PWM/etc
END_SYSEX = 0xF7            # end a MIDI SysEx msg
REPORT_VERSION = 0xF9       # report firmware version
SYSTEM_RESET = 0xFF         # reset from MIDI
QUERY_FIRMWARE = 0x79       # query the firmware name

# extended command set using sysex (0-127/0x00-0x7F)
# 0x00-0x0F reserved for user-defined commands */

EXTENDED_ANALOG = 0x6F          # analog write (PWM, Servo, etc) to any pin
PIN_STATE_QUERY = 0x6D          # ask for a pin's current mode and value
PIN_STATE_RESPONSE = 0x6E       # reply with pin's current mode and value
CAPABILITY_QUERY = 0x6B         # ask for supported modes and resolution of all pins
CAPABILITY_RESPONSE = 0x6C      # reply with supported modes and resolution
ANALOG_MAPPING_QUERY = 0x69     # ask for mapping of analog to pin numbers
ANALOG_MAPPING_RESPONSE = 0x6A  # reply with mapping info

SERVO_CONFIG = 0x70         # set max angle, minPulse, maxPulse, freq
STRING_DATA = 0x71          # a string message with 14-bits per char
PULSE_IN = 0x74             # send a pulse in command (pulseIn Firmata required)
SHIFT_DATA = 0x75           # a bitstream to/from a shift register
I2C_REQUEST = 0x76          # send an I2C read/write request
I2C_REPLY = 0x77            # a reply to an I2C read request
I2C_CONFIG = 0x78           # config I2C settings such as delay times and power pins
REPORT_FIRMWARE = 0x79      # report name and version of the firmware
SAMPLING_INTERVAL = 0x7A    # set the poll rate of the main loop
SYSEX_NON_REALTIME = 0x7E   # MIDI Reserved for non-realtime messages
SYSEX_REALTIME = 0x7F       # MIDI Reserved for realtime messages


# Pin modes.
# except from UNAVAILABLE taken from Firmata.h
UNAVAILABLE = -1
INPUT = 0          # as defined in wiring.h
OUTPUT = 1         # as defined in wiring.h
ANALOG = 2         # analog pin in analogInput mode
PWM = 3            # digital pin in PWM output mode
SERVO = 4          # digital pin in SERVO mode

# Pin types
DIGITAL = OUTPUT   # same as OUTPUT below
# ANALOG is already defined above

# Time to wait after initializing serial, used in Board.__init__
BOARD_SETUP_WAIT_TIME = 5


class PinAlreadyTakenError(Exception):
    pass


class InvalidPinDefError(Exception):
    pass


class NoInputWarning(RuntimeWarning):
    pass


class Board(object):
    """The Base class for any board."""
    firmata_version = None
    firmware = None
    firmware_version = None
    _command_handlers = {}
    _command = None
    _stored_data = []
    _parsing_sysex = False
    _iterator = None

    def __init__(self, port, layout=None, baudrate=57600, name=None, timeout=None):
        self.sp = serial.Serial(port, baudrate, timeout=timeout)
        # Allow 5 secs for Arduino's auto-reset to happen
        # Alas, Firmata blinks its version before printing it to serial
        # For 2.3, even 5 seconds might not be enough.
        # TODO Find a more reliable way to wait until the board is ready
        self.pass_time(BOARD_SETUP_WAIT_TIME)
        self.name = name
        self._layout = layout
        if not self.name:
            self.name = port

        if layout:
            self.setup_layout(layout)
        else:
            self.auto_setup()

        # Iterate over the first messages to get firmware data
        while self.bytes_available():
            self.iterate()
        # TODO Test whether we got a firmware name and version, otherwise there
        # probably isn't any Firmata installed

    def __str__(self):
        return "Board{0.name} on {0.sp.port}".format(self)

    def __del__(self):
        """
        The connection with the a board can get messed up when a script is
        closed without calling board.exit() (which closes the serial
        connection). Therefore also do it here and hope it helps.
        (It seems that it doesn't always work, it's better to use
            the with statement to be sure that exit gets called properly:

            board = Arduino('/dev/...')
            with board: # an Iterator gets started automagically.
                # Do something with the board...
            # board.exit() get's called automagically.
        """
        self.exit()

    def __enter__(self):
        """
        Allows you to use the with statement with the board.
        It will take care of starting an iterator for you.
        """
        self._iterator = Iterator(self)
        self._iterator.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Allows you to use the with statement with the board.
        This will make sure exit() gets called so the connection with
        the board doesn't get messed.
        """
        self.exit()
        self._iterator = None

    def send_as_two_bytes(self, val):
        self.sp.write(bytearray([val % 128, val >> 7]))

    def setup_layout(self, board_layout):
        """
        Setup the Pin instances based on the given board layout.
        """
        # Create pin instances based on board layout
        self.analog = []
        for i in board_layout['analog']:
            self.analog.append(Pin(self, i))

        self.digital = []
        self.digital_ports = []
        for i in range(0, len(board_layout['digital']), 8):
            num_pins = len(board_layout['digital'][i:i + 8])
            port_number = int(i / 8)
            self.digital_ports.append(Port(self, port_number, num_pins))

        # Allow to access the Pin instances directly
        for port in self.digital_ports:
            self.digital += port.pins

        # Setup PWM pins
        for i in board_layout['pwm']:
            self.digital[i].PWM_CAPABLE = True

        # Disable certain ports like Rx/Tx and crystal ports
        for i in board_layout['disabled']:
            self.digital[i].mode = UNAVAILABLE

        # Create a dictionary of 'taken' pins. Used by the get_pin method
        self.taken = {'analog': dict(map(lambda p: (p.pin_number, False), self.analog)),
                      'digital': dict(map(lambda p: (p.pin_number, False), self.digital))}

        self._set_default_handlers()

    def _set_default_handlers(self):
        # Setup default handlers for standard incoming commands
        self.add_cmd_handler(ANALOG_MESSAGE, self._handle_analog_message)
        self.add_cmd_handler(DIGITAL_MESSAGE, self._handle_digital_message)
        self.add_cmd_handler(REPORT_VERSION, self._handle_report_version)
        self.add_cmd_handler(REPORT_FIRMWARE, self._handle_report_firmware)
        self.add_cmd_handler(PULSE_IN, self._handle_pulse_in)

    def auto_setup(self):
        """
        Automatic setup based on Firmata's "Capability Query"
        """
        self.add_cmd_handler(CAPABILITY_RESPONSE, self._handle_report_capability_response)
        self.send_sysex(CAPABILITY_QUERY, [])
        self.pass_time(0.1) # Serial SYNC

        while self.bytes_available():
            self.iterate()

        # handle_report_capability_response will write self._layout
        if self._layout:
            self.setup_layout(self._layout)
        else:
            raise IOError("Board detection failed.")

    def add_cmd_handler(self, cmd, func):
        """Adds a command handler for a command."""
        len_args = len(inspect.getargspec(func)[0])

        def add_meta(f):
            def decorator(*args, **kwargs):
                f(*args, **kwargs)
            decorator.bytes_needed = len_args - 1  # exclude self
            decorator.__name__ = f.__name__
            return decorator
        func = add_meta(func)
        self._command_handlers[cmd] = func

    def get_pin(self, pin_def):
        """
        Returns the activated pin given by the pin definition.
        May raise an ``InvalidPinDefError`` or a ``PinAlreadyTakenError``.

        :arg pin_def: Pin definition as described below,
            but without the arduino name. So for example ``a:1:i``.

        'a' analog pin     Pin number   'i' for input
        'd' digital pin    Pin number   'o' for output
                                        'p' for pwm (Pulse-width modulation)

        All seperated by ``:``.
        """
        if type(pin_def) == list:
            bits = pin_def
        else:
            bits = pin_def.split(':')
        a_d = bits[0] == 'a' and 'analog' or 'digital'
        part = getattr(self, a_d)
        pin_nr = int(bits[1])
        if pin_nr >= len(part):
            raise InvalidPinDefError('Invalid pin definition: {0} at position 3 on {1}'.format(pin_def, self.name))
        if getattr(part[pin_nr], 'mode', None) == UNAVAILABLE:
            raise InvalidPinDefError('Invalid pin definition: UNAVAILABLE pin {0} at position on {1}'.format(pin_def, self.name))
        if self.taken[a_d][pin_nr]:
            raise PinAlreadyTakenError('{0} pin {1} is already taken on {2}'.format(a_d, bits[1], self.name))
        # ok, should be available
        pin = part[pin_nr]
        self.taken[a_d][pin_nr] = True
        if pin.type is DIGITAL:
            if bits[2] == 'p':
                pin.mode = PWM
            elif bits[2] == 's':
                pin.mode = SERVO
            elif bits[2] != 'o':
                pin.mode = INPUT
        else:
            pin.enable_reporting()
        return pin

    def pass_time(self, t):
        """Non-blocking time-out for ``t`` seconds."""
        cont = time.time() + t
        while time.time() < cont:
            time.sleep(0)

    def send_sysex(self, sysex_cmd, data):
        """
        Sends a SysEx msg.

        :arg sysex_cmd: A sysex command byte
        : arg data: a bytearray of 7-bit bytes of arbitrary data
        """
        msg = bytearray([START_SYSEX, sysex_cmd])
        msg.extend(data)
        msg.append(END_SYSEX)
        self.sp.write(msg)

    def bytes_available(self):
        return self.sp.inWaiting()

    def iterate(self):
        """
        Reads and handles data from the microcontroller over the serial port.
        This method should be called in a main loop or in an :class:`Iterator`
        instance to keep this boards pin values up to date.
        """
        byte = self.sp.read()
        if not byte:
            return
        data = ord(byte)
        received_data = []
        handler = None
        if data < START_SYSEX:
            # These commands can have 'channel data' like a pin nummber appended.
            try:
                handler = self._command_handlers[data & 0xF0]
            except KeyError:
                return
            received_data.append(data & 0x0F)
            try:
                while len(received_data) < handler.bytes_needed:
                    received_data.append(ord(self.sp.read()))
            except TypeError:
                # We'll probably get a
                # "TypeError: ord() expected a character, but string of length 0 found"
                # if any self.sp.read() fails due to a timeout.
                raise IOError("Failed to read 'channel' data from port, " \
                                + "read %s bytes expected %s bytes" %
                                    (len(received_data), handler.bytes_needed))
        elif data == START_SYSEX:
            data = ord(self.sp.read())
            handler = self._command_handlers.get(data)
            if not handler:
                return
            data = ord(self.sp.read())
            while data != END_SYSEX:
                received_data.append(data)
                data = ord(self.sp.read())
        else:
            try:
                handler = self._command_handlers[data]
            except KeyError:
                return
            try:
                while len(received_data) < handler.bytes_needed:
                    received_data.append(ord(self.sp.read()))
            except TypeError:
                # We'll probably get a
                # "TypeError: ord() expected a character, but string of length 0 found"
                # if any self.sp.read() fails due to a timeout.
                raise IOError("Failed to read data from port, " \
                                + "read %s bytes expected %s bytes" %
                                    (len(received_data), handler.bytes_needed))

        # Handle the data
        try:
            handler(*received_data)
        except ValueError:
            pass

    def get_firmata_version(self):
        """
        Returns a version tuple (major, minor) for the firmata firmware on the
        board.
        """
        return self.firmata_version

    def servo_config(self, pin, min_pulse=544, max_pulse=2400, angle=0):
        """
        Configure a pin as servo with min_pulse, max_pulse and first angle.
        ``min_pulse`` and ``max_pulse`` default to the arduino defaults.
        """
        if pin > len(self.digital) or self.digital[pin].mode == UNAVAILABLE:
            raise IOError("Pin {0} is not a valid servo pin".format(pin))

        data = bytearray([pin])
        data += to_two_bytes(min_pulse)
        data += to_two_bytes(max_pulse)
        self.send_sysex(SERVO_CONFIG, data)

        # set pin._mode to SERVO so that it sends analog messages
        # don't set pin.mode as that calls this method
        self.digital[pin]._mode = SERVO
        self.digital[pin].write(angle)

    def exit(self):
        """Call this to exit cleanly."""
        # First detach all servo's, otherwise it somehow doesn't want to close...
        if hasattr(self, 'digital'):
            for pin in self.digital:
                if pin.mode == SERVO:
                    pin.mode = OUTPUT
        if hasattr(self, 'sp'):
            self.sp.close()

    # Command handlers
    def _handle_analog_message(self, pin_nr, lsb, msb):
        value = round(float((msb << 7) + lsb) / 1023, 4)
        # Only set the value if we are actually reporting
        try:
            if self.analog[pin_nr].reporting:
                self.analog[pin_nr].value = value
        except IndexError:
            raise ValueError

    def _handle_digital_message(self, port_nr, lsb, msb):
        """
        Digital messages always go by the whole port. This means we have a
        bitmask which we update the port.
        """
        mask = (msb << 7) + lsb
        try:
            self.digital_ports[port_nr]._update(mask)
        except IndexError:
            raise ValueError

    def _handle_report_version(self, major, minor):
        self.firmata_version = (major, minor)

    def _handle_report_firmware(self, *data):
        major = data[0]
        minor = data[1]
        self.firmware_version = (major, minor)
        self.firmware = two_byte_iter_to_str(data[2:])

    def _handle_report_capability_response(self, *data):
        charbuffer = []
        pin_spec_list = []

        for c in data:
            if c == CAPABILITY_RESPONSE:
                continue

            charbuffer.append(c)
            if c == 0x7F:
                # A copy of charbuffer
                pin_spec_list.append(charbuffer[:])
                charbuffer = []

        self._layout = pin_list_to_board_dict(pin_spec_list)

    #
    # Handle PULSE_IN sysex responses.
    # Requires pulseIn compatible Firmata in the arduino board
    # (see https://github.com/jgautier/arduino-1/tree/pulseIn).
    # Used with HC-SR04 ultrasonic ranging sensors
    # (see http://www.micropik.com/PDF/HCSR04.pdf).
    #
    def _handle_pulse_in(self, pin_nr, *data):
        duration = (from_two_bytes(data[1:3]) << 24) \
                    + (from_two_bytes(data[3:5]) << 16) \
                    + (from_two_bytes(data[5:7]) << 8) \
                    + from_two_bytes(data[7:9])
        self.digital[pin_nr].last_pulse_in_duration = duration
        # We can calculate the distance using an HC-SR04 as 'duration / 58.2'

class Port(object):
    """An 8-bit port on the board."""
    def __init__(self, board, port_number, num_pins=8):
        self.board = board
        self.port_number = port_number
        self.reporting = False

        self.pins = []
        for i in range(num_pins):
            pin_nr = i + self.port_number * 8
            self.pins.append(Pin(self.board, pin_nr, type=DIGITAL, port=self))

    def __str__(self):
        return "Digital Port {0.port_number} on {0.board}".format(self)

    def enable_reporting(self):
        """Enable reporting of values for the whole port."""
        self.reporting = True
        msg = bytearray([REPORT_DIGITAL + self.port_number, 1])
        self.board.sp.write(msg)

        for pin in self.pins:
            if pin.mode == INPUT:
                pin.reporting = True  # TODO Shouldn't this happen at the pin?

    def disable_reporting(self):
        """Disable the reporting of the port."""
        self.reporting = False
        msg = bytearray([REPORT_DIGITAL + self.port_number, 0])
        self.board.sp.write(msg)

    def write(self):
        """Set the output pins of the port to the correct state."""
        mask = 0
        for pin in self.pins:
            if pin.mode == OUTPUT:
                if pin.value == 1:
                    pin_nr = pin.pin_number - self.port_number * 8
                    mask |= 1 << int(pin_nr)
#        print("type mask", type(mask))
#        print("type self.portnumber", type(self.port_number))
#        print("type pinnr", type(pin_nr))
        msg = bytearray([DIGITAL_MESSAGE + self.port_number, mask % 128, mask >> 7])
        self.board.sp.write(msg)

    def _update(self, mask):
        """Update the values for the pins marked as input with the mask."""
        if self.reporting:
            for pin in self.pins:
                if pin.mode is INPUT:
                    pin_nr = pin.pin_number - self.port_number * 8
                    pin.value = (mask & (1 << pin_nr)) > 0


class Pin(object):
    """A Pin representation"""
    def __init__(self, board, pin_number, type=ANALOG, port=None):
        self.board = board
        self.pin_number = pin_number
        self.type = type
        self.port = port
        self.PWM_CAPABLE = False
        self._mode = (type == DIGITAL and OUTPUT or INPUT)
        self.reporting = False
        self.value = None
        self.last_pulse_in_duration = None

    def __str__(self):
        type = {ANALOG: 'Analog', DIGITAL: 'Digital'}[self.type]
        return "{0} pin {1}".format(type, self.pin_number)

    def _set_mode(self, mode):
        if mode is UNAVAILABLE:
            self._mode = UNAVAILABLE
            return
        if self._mode is UNAVAILABLE:
            raise IOError("{0} can not be used through Firmata".format(self))
        if mode is PWM and not self.PWM_CAPABLE:
            raise IOError("{0} does not have PWM capabilities".format(self))
        if mode == SERVO:
            if self.type != DIGITAL:
                raise IOError("Only digital pins can drive servos! {0} is not"
                    "digital".format(self))
            self._mode = SERVO
            self.board.servo_config(self.pin_number)
            return

        # Set mode with SET_PIN_MODE message
        self._mode = mode
        self.board.sp.write(bytearray([SET_PIN_MODE, self.pin_number, mode]))
        if mode == INPUT:
            self.enable_reporting()

    def _get_mode(self):
        return self._mode

    mode = property(_get_mode, _set_mode)
    """
    Mode of operation for the pin. Can be one of the pin modes: INPUT, OUTPUT,
    ANALOG, PWM. or SERVO (or UNAVAILABLE).
    """

    def enable_reporting(self):
        """Set an input pin to report values."""
        if self.mode is not INPUT:
            raise IOError("{0} is not an input and can therefore not report".format(self))
        if self.type == ANALOG:
            self.reporting = True
            msg = bytearray([REPORT_ANALOG + self.pin_number, 1])
            self.board.sp.write(msg)
        else:
            self.port.enable_reporting()
            # TODO This is not going to work for non-optimized boards like Mega

    def disable_reporting(self):
        """Disable the reporting of an input pin."""
        if self.type == ANALOG:
            self.reporting = False
            msg = bytearray([REPORT_ANALOG + self.pin_number, 0])
            self.board.sp.write(msg)
        else:
            self.port.disable_reporting()
            # TODO This is not going to work for non-optimized boards like Mega

    def read(self):
        """
        Returns the output value of the pin. This value is updated by the
        boards :meth:`Board.iterate` method. Value is always in the range from
        0.0 to 1.0.
        """
        if self.mode == UNAVAILABLE:
            raise IOError("Cannot read pin {0}".format(self.__str__()))
        return self.value

    def write(self, value):
        """
        Output a voltage from the pin

        :arg value: Uses value as a boolean if the pin is in output mode, or
            expects a float from 0 to 1 if the pin is in PWM mode. If the pin
            is in SERVO the value should be in degrees.

        """
        if self.mode is UNAVAILABLE:
            raise IOError("{0} can not be used through Firmata".format(self))
        if self.mode is INPUT:
            raise IOError("{0} is set up as an INPUT and can therefore not be written to".format(self))
        if value is not self.value:
            self.value = value
            if self.mode is OUTPUT:
                if self.port:
                    self.port.write()
                else:
                    msg = bytearray([DIGITAL_MESSAGE, self.pin_number, value])
                    self.board.sp.write(msg)
            elif self.mode is PWM:
                value = int(round(value * 255))
                msg = bytearray([ANALOG_MESSAGE + self.pin_number, value % 128, value >> 7])
                self.board.sp.write(msg)
            elif self.mode is SERVO:
                value = int(value)
                msg = bytearray([ANALOG_MESSAGE + self.pin_number, value % 128, value >> 7])
                self.board.sp.write(msg)

    def ping(self, trigger_mode=1, trigger_duration=10, echo_timeout=65000):
        """
        Trigger the pin and wait for a pulseIn echo.

        Used with HC-SR04 ultrasonic ranging sensors
        (see http://www.micropik.com/PDF/HCSR04.pdf).

        Note: Requires pulseIn compatible Firmata in the arduino board
              (see https://github.com/jgautier/arduino-1/tree/pulseIn).

        :arg trigger_mode: Uses value as a boolean,
                        0 to trigger LOW,
                        1 to trigger HIGH (default, for HC-SR04 modules).
        :arg trigger_duration: Duration (us) for the trigger signal.
        :arg echo_timeout: Time (us) to wait for the echo (pulseIn timeout).
        """
        if self.mode is not OUTPUT:
            raise IOError("{0} should be in OUTPUT mode".format(self))
        if trigger_mode not in (0, 1):
            raise IOError("trigger_mode should be 0 or 1")

        # This is the protocol to ask for a pulseIn:
        #       START_SYSEX(0xF0)           // send_sysex(...)
        #       puseIn/pulseOut(0x74)       // send_sysex(PULSE_IN, ...)
        #       pin(0-127)
        #       value(1 or 0, HIGH or LOW)
        #       pulseOutDuration 0 (LSB)
        #       pulseOutDuration 0 (MSB)
        #       pulseOutDuration 1 (LSB)
        #       pulseOutDuration 1 (MSB)
        #       pulseOutDuration 2 (LSB)
        #       pulseOutDuration 2 (MSB)
        #       pulseOutDuration 3 (LSB)
        #       pulseOutDuration 3 (MSB)
        #       pulseInTimeout 0 (LSB)
        #       pulseInTimeout 0 (MSB)
        #       pulseInTimeout 1 (LSB)
        #       pulseInTimeout 1 (MSB)
        #       pulseInTimeout 2 (LSB)
        #       pulseInTimeout 2 (MSB)
        #       pulseInTimeout 3 (LSB)
        #       pulseInTimeout 3 (MSB)
        #       END_SYSEX(0xF7)             // send_sysex(...)

        data = bytearray()
        data.append(self.pin_number)    # Pin number
        data.append(trigger_mode)       # Trigger mode (1 or 0, HIGH or LOW)
        trigger_duration_arr = to_two_bytes((trigger_duration >> 24) & 0xFF) \
                             + to_two_bytes((trigger_duration >> 16) & 0xFF) \
                             + to_two_bytes((trigger_duration >> 8) & 0xFF) \
                             + to_two_bytes(trigger_duration & 0xFF)
        data.extend(trigger_duration_arr)   # pulseOutDuration
        echo_timeout_arr = to_two_bytes((echo_timeout >> 24) & 0xFF) \
                             + to_two_bytes((echo_timeout >> 16) & 0xFF) \
                             + to_two_bytes((echo_timeout >> 8) & 0xFF) \
                             + to_two_bytes(echo_timeout & 0xFF)
        data.extend(echo_timeout_arr)       # pulseInTimeout

        self.last_pulse_in_duration = None
        self.board.send_sysex(PULSE_IN, data)

        # Wait for the reply...
        waited_for = 0
        while self.last_pulse_in_duration is None \
                    and waited_for < (echo_timeout + trigger_duration) / 1000.0 ** 2:
            time.sleep(0.01) # Sleep for 10 milliseconds
            waited_for = waited_for + 0.01

        return self.last_pulse_in_duration
