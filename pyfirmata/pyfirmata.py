from __future__ import division
from __future__ import unicode_literals
import inspect
import time

import serial

from .util import two_byte_iter_to_str, to_two_bytes

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
SERVO_CONFIG = 0x70         # set max angle, minPulse, maxPulse, freq
STRING_DATA = 0x71          # a string message with 14-bits per char
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
SHIFT = 5          # shiftIn/shiftOut mode
I2C = 6            # pin can function as I2C pin (SDL or SDA)

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
    """
    Base class for any board
    """
    firmata_version = None
    firmware = None
    firmware_version = None
    pins = {}           # stores Pin instances (including Rx, Tx, analog)
    ports = {}          # stores Port instance information
    analog_pins = {}    # maps analog pin number to 'generic' Pin instance
    _command_handlers = {}
    _command = None
    _stored_data = []
    _parsing_sysex = False
    
    
    def __init__(self, port, layout, baudrate=57600, name=None):
        self.sp = serial.Serial(port, baudrate)
        # Allow 5 secs for Arduino's auto-reset to happen
        # Alas, Firmata blinks it's version before printing it to serial
        # For 2.3, even 5 seconds might not be enough.
        # TODO Find a more reliable way to wait until the board is ready
        self.pass_time(BOARD_SETUP_WAIT_TIME)
        self.name = name
        if not self.name:
            self.name = port

        # Setup default handlers for standard incoming commands
        self.add_cmd_handler(ANALOG_MESSAGE, self._handle_analog_message)
        self.add_cmd_handler(DIGITAL_MESSAGE, self._handle_digital_message)
        self.add_cmd_handler(REPORT_VERSION, self._handle_report_version)
        self.add_cmd_handler(REPORT_FIRMWARE, self._handle_report_firmware)

        self.setup_layout(layout)
        # Iterate over the first messages to get firmware data
        while self.bytes_available():
            self.iterate()
        # TODO Test whether we got a firmware name and version, otherwise there 
        # probably isn't any Firmata installed
        
    def __str__(self):
        return "Board{0.name} on {0.sp.port}".format(self)
        
    def __del__(self):
        ''' 
        The connection with the a board can get messed up when a script is
        closed without calling board.exit() (which closes the serial
        connection). Therefore also do it here and hope it helps.
        '''
        self.exit()
        
    def send_as_two_bytes(self, val):
        self.sp.write(bytearray([val % 128, val >> 7]))

    def setup_layout(self, board_layout):
        """
        Setup the Pin instances based on a predefined board-layout as 
        described in ``boards.py``. 
        """
        # Assume that every digital port has INPUT, OUTPUT mode
        # Number of pins is equal to the digital pins available (including 
        # UNAVAILABLE pins (Rx, Tx) to keep in line with the 'autodetect' 
        # functionality that does report such pins)
        for nr in board_layout['digital']:
            self.pins[nr] = Pin(self, nr)
            self.pins[nr].input_capable = True
            self.pins[nr].output_capable = True

        # Mark any unavailable pins
        for nr in board_layout['unavailable']:
            self.pins[nr].mode = UNAVAILABLE

        # Mark PWM, SERVO, I2C pins:
        for nr in board_layout['pwm']:
            self.pins[nr].pwm_capable = True
        for nr in board_layout['i2c']:
            self.pins[nr].i2c_capable = True
        for nr in board_layout['servo']:
            self.pins[nr].servo_capable = True

        # mark Analog pins
        for nr in board_layout['analog']:
            self.pins[nr].analog_capable = True

        # Create an Analog to Digital mapping. Assume the first pin with 
        # Analog_capable is A0, the next A1, etc. This code duplicates 
        # the code of the ``_handle_analog_mapping_query``. 
        #
        # Step 1. Get all the digital pin numbers. Note that it is not 
        #         guaranteed that the pin numbers are in sequential order
        #         or start with 0 -- should be board-agnostic.
        pin_nrs = []
        for pin in self.pins:
            pin_nrs.append(self.pins[pin].pin_number)
        pin_nrs = sorted(pin_nrs)

        # Step 2. For each of the pins detected, find their associated analog pin.
        curr_analog_counter = 0
        for dig_pin_nr in pin_nrs:
            if self.pins[dig_pin_nr].analog_capable == True:
                self.analog_pins[curr_analog_counter] = self.pins[dig_pin_nr]
                self.analog_pins[curr_analog_counter].analog_queried = curr_analog_counter
                curr_analog_counter += 1

        # bin the pins to ports. Identical as in 'autodetect' function
        total_ports = divmod(len(self.pins), 8)[0] + 1
        for port_nr in range(total_ports):
            pins_in_this_port = pin_nrs[0 + port_nr*8:8 + port_nr*8]
            self.ports[port_nr] = Port(self, port_nr, pins_in_this_port)

    
    def add_cmd_handler(self, cmd, func):
        """ 
        Adds a command handler for a command.
        """
        len_args = len(inspect.getargspec(func)[0])
        def add_meta(f):
            def decorator(*args, **kwargs):
                f(*args, **kwargs)
            decorator.bytes_needed = len_args - 1 # exclude self
            decorator.__name__ = f.__name__
            return decorator
        func = add_meta(func)
        self._command_handlers[cmd] = func
        
    def get_pin(self, pin_def):
        """
        Returns the activated pin given by the pin definition.
        May raise an ``InvalidPinDefError`` or a ``PinAlreadyTakenError``.
        
        :arg pin_def: Pin definition as described in TODO,
            but without the arduino name. So for example ``a:1:i``.
        
        """
        if type(pin_def) == list:
            bits = pin_def
        else:
            bits = pin_def.split(':')
        
        a_d = bits[0]
        pin_nr = int(bits[1])
        new_mode = bits[2]

        # Do some tests before we attempt to grab a pin number
        if a_d not in ['a', 'd']:
            raise InvalidPinDefError("Command does not start with 'a' or 'd'")
        if a_d == 'a' and pin_nr not in self.analog_pins:
            raise InvalidPinDefError("There is no analog pin with number {0}".format(pin_nr))
        elif a_d == 'd' and pin_nr not in self.pins:
            raise InvalidPinDefError("There is no digital pin with number {0}".format(pin_nr))

        # The pin exists, so lets grab the pin instance.
        if a_d == 'a':
            curr_pin = self.analog_pins[pin_nr]
        else:
            curr_pin = self.pins[pin_nr]

        # Check if the pin instance can be used: not TAKEN, UNAVAILABLE
        if curr_pin.mode == UNAVAILABLE:
            raise InvalidPinDefError("Pin {0} is marked as being UNAVAILABLE".format(pin_nr))
        if curr_pin.taken:
            raise PinAlreadyTakenError("{0} pin {1} has been taken already".format(a_d, pin_nr))

        # ok, we can use this pin instance
        # Note that pin type checking (digital/analog) happens in in Pin._set_mode()
        if new_mode == 'p':
            curr_pin.mode = PWM
        elif new_mode == 's':
            curr_pin.mode = SERVO
        elif new_mode == 'o':
            curr_pin.mode = OUTPUT
        elif new_mode == 'i':
            if a_d == 'a':
                curr_pin.mode = ANALOG
            else:
                curr_pin.mode = INPUT
        elif new_mode == 'a':
            curr_pin.mode = ANALOG
        elif new_mode == 'i2c':
            curr_pin.mode = I2C

       # If analog or digital_input, run enable_reporting
#        curr_pin.enable_reporting()

        return curr_pin         # return the pin instance


    def pass_time(self, t):
        """ 
        Non-blocking time-out for ``t`` seconds.
        """
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
        This method should be called in a main loop, or in an
        :class:`Iterator` instance to keep this boards pin values up to date
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
            while len(received_data) < handler.bytes_needed:
                received_data.append(ord(self.sp.read()))
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
            while len(received_data) < handler.bytes_needed:
                received_data.append(ord(self.sp.read()))
        # Handle the data
        try:
            handler(*received_data)
        except ValueError:
            pass
            
    def get_firmata_version(self):
        """
        Returns a version tuple (major, mino) for the firmata firmware on the
        board.
        """
        return self.firmata_version
        
    def servo_config(self, pin, min_pulse=544, max_pulse=2400, angle=0):
        """
        Configure a pin as servo with min_pulse, max_pulse and first angle.
        ``min_pulse`` and ``max_pulse`` default to the arduino defaults.
        """
        if self.pins[pin].servo_capable == False:
            raise IOError("Pin {0} is not a valid servo pin".format(pin))
        if self.pins[pin].mode == UNAVAILABLE:
            raise IOError("Pin {0} is UNAVAILABLE for Servo use".format(pin))

        data = bytearray([pin])
        data += to_two_bytes(min_pulse)
        data += to_two_bytes(max_pulse)
        self.send_sysex(SERVO_CONFIG, data)
        
        # set pin._mode to SERVO so that it sends analog messages
        # don't set pin.mode as that calls this method
        self.pins[pin]._mode = SERVO
        self.pins[pin].write(angle)

        
    def exit(self):
        """ Call this to exit cleanly. """
        # First detach all servo's, otherwise it somehow doesn't want to close...
        # FIXME
        for pin in self.pins:
            if self.pins[pin].mode == SERVO:
                self.pins[pin].mode = OUTPUT
        if hasattr(self, 'sp'):
            self.sp.close()
        # the following lines are added to aid with the TestSuite
        # clearing all references to the pins and ports will ensure
        # that all data is removed. This should also solve the mysterious
        # behavior that at times, data is present in 'fresh' board instances
        self.pins.clear()
        self.ports.clear()


    # Command handlers
    def _handle_analog_message(self, pin_nr, lsb, msb):
        value = round(float((msb << 7) + lsb) / 1023, 4)
        # Only set the value if we are actually reporting
        try:
            if self.analog_pins[pin_nr].reporting:
                self.analog_pins[pin_nr].value = value
        except IndexError:
            raise ValueError

    def _handle_digital_message(self, port_nr, lsb, msb):
        """
        Digital messages always go by the whole port. This means we have a
        bitmask wich we update the port.
        """
        mask = (msb << 7) + lsb
        try:
            self.ports[port_nr]._update(mask)
        except IndexError:
            raise ValueError

    def _handle_report_version(self, major, minor):
        self.firmata_version = (major, minor)
        
    def _handle_report_firmware(self, *data):
        major = data[0]
        minor = data[1]
        self.firmware_version = (major, minor)
        self.firmware = two_byte_iter_to_str(data[2:])


class Port(object):
    """ An 8-bit port on the board """
    def __init__(self, board, port_number, pins):
        self.board = board
        self.port_number = port_number
        self.pins = tuple(pins)
        self.reporting = False

    def __str__(self):
        return "Digital Port {0.port_number} on {0.board}".format(self)
        
    def enable_reporting(self):
        """ Enable reporting of values for the whole port """
        self.reporting = True
        msg = bytearray([REPORT_DIGITAL + self.port_number, 1])
        self.board.sp.write(msg)

        for pin in self.pins:
            if self.board.pins[pin].mode == INPUT:
                self.board.pins[pin].reporting = True # TODO Shouldn't this happen at the pin?

        
    def disable_reporting(self):
        """ Disable the reporting of the port """
        self.reporting = False
        msg = bytearray([REPORT_DIGITAL + self.port_number, 0])
        self.board.sp.write(msg)
        
        for pin in self.pins:
            if self.board.pins[pin] == INPUT:
                self.board.pins[pin].reporting = False
                

    def write(self):
        """Set the output pins of the port to the correct state"""
        mask = 0
        # only report for pins that are taken, and OUTPUT, and have value 
        for pin in self.pins:
            if self.board.pins[pin].taken == True:
                if self.board.pins[pin].mode == OUTPUT:
                    if self.board.pins[pin].value == 1:
                        pin_nr = self.pins.index(pin)
                        mask |= 1 << pin_nr
        
        msg = bytearray([DIGITAL_MESSAGE + self.port_number, mask % 128, mask >> 7])
        self.board.sp.write(msg)
       
    def _update(self, mask):
        """
        Update the values for the pins marked as input with the mask.
        """
        if self.reporting:
            for pin in self.pins:
                if self.board.pins[pin].mode == INPUT:
                    pin_nr = self.pins.index(pin)
                    self.board.pins[pin].value = (mask & (1 << pin_nr)) > 0


class Pin(object):
    """ A Pin representation 
    
    Each 'pin' instance is linked to a physical pin on the board. 
    It stores information about its own state, value, capabilities, etc.,
    but does not necessarily know a lot about other Pins, Ports, and the board.
    """
    def __init__(self, board, pin_number):
        self.board = board
        self.pin_number = pin_number
        self.value = None
        self.reporting = False
        self.taken = False
        self._mode = INPUT           # See http://arduino.cc/en/Tutorial/DigitalPins:
                                     # 'Arduino (Atmega) pins default to inputs (...)'
        self.input_capable = False
        self.output_capable = False
        self.analog_capable = False
        self.analog_queried = None
        self.pwm_capable = False
        self.servo_capable = False
        self.i2c_capable = False

        
    def __str__(self):
        """Print Pin information in readable format"""
        return "Pin {0.pin_number}, mode {0.mode}, value {0.value}".format(self)


    def _set_mode(self, new_mode):
        """Setter function for the pin mode"""
        # Some sanity checks
        if new_mode not in [UNAVAILABLE, INPUT, OUTPUT, ANALOG, PWM, SERVO, I2C]:
            raise InvalidPinDefError("Mode {0} is not recognized".format(new_mode))
        if self._mode in [UNAVAILABLE]:
            raise InvalidPinDefError("Pin {0} is UNAVAILABLE".format(self.pin_number))
        if self.taken == True:
            print("WARNING: Pin {0} is already taken".format(self.pin_number))

        # Set the mode
        if new_mode == UNAVAILABLE:
            # Make sure no function accidently will use any of the Boolean indicators
            self._mode = UNAVAILABLE
            self.taken = True
            self.reporting = False
            self.value = None
            return
        elif new_mode == INPUT:
            if self.input_capable:
                self._mode = INPUT
                self.reporting = False      # reporting is set per digital port
                self.taken = True
            else:
                raise InvalidPinDefError("Pin {0} has no INPUT mode".format(self.pin_number))
        elif new_mode == OUTPUT:
            if self.output_capable:
                self._mode = OUTPUT
                self.taken = True
                self.reporting = False
            else:
                raise InvalidPinDefError("ERROR: Pin {0} has no OUTPUT mode".format(self.pin_number))
        elif new_mode == ANALOG:
            if self.analog_capable:
                self._mode = ANALOG
                self.reporting = False
                self.taken = True
            else:
                print("WARNING: Pin {0} has no ANALOG mode".format(self.pin_number))
        elif new_mode == SERVO:
            if self.servo_capable:
                self._mode = SERVO
                self.taken = True
                self.reporting = False
            else:
                raise InvalidPinDefError("ERROR: Pin {0} is not SERVO capable".format(self.pin_number))
        elif new_mode == PWM:
            if self.pwm_capable:
                self.taken = True
                self._mode = PWM
                self.reporting = False
            else:
                raise InvalidPinDefError("ERROR: Pin {0} is not PWM capable".format(self.pin_number))
        elif new_mode == I2C:
            if self.i2c_capable:
                self.taken = True
                self._mode = I2C
                self.reporting = False
                self.value = None
            else:
                raise InvalidPinDefError("ERROR: Pin {0} is not I2C capable".format(self.pin_number))

        self.board.sp.write(bytearray([SET_PIN_MODE, self.pin_number, self.mode]))
        self.enable_reporting()

        
    def _get_mode(self):
        return self._mode
        
    mode = property(_get_mode, _set_mode)
    """
    Mode of operation for the pin. Can be one of the pin modes: INPUT, OUTPUT,
    ANALOG, PWM, SERVO, I2C (or UNAVAILABLE)
    """
    
    def enable_reporting(self):
        """ Set an input pin to report values """
        # Firmata protocol: analog reporting goes per pin
        if self.analog_capable and self.mode == ANALOG:
            self.reporting = True
            msg = bytearray([REPORT_ANALOG + self.analog_queried, 1])
            self.board.sp.write(msg)

        # Firmata protocol: digital reporting goes per port
        if self.input_capable and self.mode == INPUT:
            curr_port = self.get_port()
            self.board.ports[curr_port].enable_reporting()

        
    def disable_reporting(self):
        """ Disable the reporting of an input pin """
        if self.mode == ANALOG:
            self.reporting = False
            msg = bytearray([REPORT_ANALOG + self.analog_queried, 0])
            self.board.sp.write(msg)
        else:
            curr_port = self.get_port()
            self.board.ports[curr_port].disable_reporting()


    def get_port(self):
        """Return the Port instance to which this Pin instance belongs to"""
        for myPort in self.board.ports:
            if self.pin_number in self.board.ports[myPort].pins:
                return myPort

        raise InvalidPinDefError("ERROR: pin {0} is not assigned to any port.".format(self.pin_number))


    def read(self):
        """
        Returns the output value of the pin. This value is updated by the
        boards :meth:`Board.iterate` method. Value is alway in the range 0.0 - 1.0
        """
        # Check if pin is unavailable, or taken, or not tagged for reporting.
        if self.mode == UNAVAILABLE:
            raise InvalidPinDefError("Pin {0} is UNAVAILABLE".format(self.pin_number))
        if self.taken is False:
            raise InvalidPinDefError("Pin {0} is not yet taken, value is undetermined. Use 'setPin()' command first".format(self.pin_number))
        if self.reporting == False:
            raise InvalidPinDefError("Pin {0} has 'reporting' set to False".format(self.pin_number))

        return self.value


    def write(self, value):
        """
        Output a voltage from the pin

        :arg value: Uses value as a boolean if the pin is in output mode, or
            expects a float from 0 to 1 if the pin is in PWM mode. If the pin 
            is in SERVO the value should be in degrees.
        
        """
        if self.mode is UNAVAILABLE:
            raise IOError("ERROR: Pin {0} can not be used ".format(self.pin_number))
        if self.mode is INPUT:
            raise IOError("ERROR: Pin {0} is set up as an INPUT and can therefore not be written to".format(self.pin_number))

        if value is not self.value:
            self.value = value

            if self.mode is OUTPUT:
                # Change value to boolean
                self.value = int(round(self.value))
                # find to which Port this pin belongs to
                curr_port = self.get_port()
                self.board.ports[curr_port].write()
            elif self.mode is PWM:
                value = int(round(value * 255))
                msg = bytearray([ANALOG_MESSAGE + self.pin_number, value % 128, value >> 7])
                self.board.sp.write(msg)
            elif self.mode is SERVO:
                value = int(value)
                msg = bytearray([ANALOG_MESSAGE + self.pin_number, value % 128, value >> 7])
                self.board.sp.write(msg)
