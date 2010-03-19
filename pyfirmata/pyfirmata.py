import serial
import inspect
import time
from boards import BOARDS

# Message command bytes - straight from Firmata.h
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

# Pin types
DIGITAL = OUTPUT   # same as OUTPUT below
# ANALOG is already defined above

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
    _command_handlers = {}
    _command = None
    _stored_data = []
    _parsing_sysex = False
    
    def __init__(self, port, type="arduino", baudrate=57600):
        self.sp = serial.Serial(port, baudrate)
        # Allow 2 secs for Arduino's auto-reset to happen
        self.pass_time(2)
        self.type = type
        self.setup_layout(BOARDS[type])
        
    def __str__(self):
        return "Board (%s) on %s" % (self.type, self.sp.port)
        
    def __del__(self):
        ''' 
        The connection with the a board can get messed up when a script is
        closed without calling board.exit() (which closes the serial
        connection). Therefore also do it here and hope it helps.
        '''
        self.exit()
        
    def send_as_two_bytes(self, val):
        self.sp.write(chr(val % 128) + chr(val >> 7))
        
    def received_as_two_bytes(self, bytes):
        lsb, msb = bytes
        return msb << 7 | lsb
        
    def setup_layout(self, board_layout):
        """
        Setup the Pin instances based on the given board-layout. Maybe it will
        be possible to do this automatically in the future, by polling the
        board for its type.
        """
        # Create pin instances based on board layout
        self.analog = []
        for i in board_layout['analog']:
            self.analog.append(Pin(self, i))
        # Only create digital ports if the Firmata can use them (ie. not on the Mega...)
        # TODO Why is (TOTAL_FIRMATA_PINS + 7) / 8 used in Firmata?
        if board_layout['use_ports']:
            self.digital = []
            self.digital_ports = []
            for i in range(len(board_layout['digital']) / 7):
                self.digital_ports.append(Port(self, i))
            # Allow to access the Pin instances directly
            for port in self.digital_ports:
                self.digital += port.pins
            for i in board_layout['pwm']:
                self.digital[i].PWM_CAPABLE = True
        else:
            self.digital = []
            for i in board_layout['digital']:
                self.digital.append(Pin(self.sp, i, type=DIGITAL))
        # Disable certain ports like Rx/Tx and crystal ports
        for i in board_layout['disabled']:
            self.digital[i].mode = UNAVAILABLE
        # Create a dictionary of 'taken' pins. Used by the get_pin method
        self.taken = { 'analog' : dict(map(lambda p: (p.pin_number, False), self.analog)),
                       'digital' : dict(map(lambda p: (p.pin_number, False), self.digital)) }
        # Setup default handlers for standard incoming commands
        self.add_cmd_handler(ANALOG_MESSAGE, self._handle_analog_message)
        self.add_cmd_handler(DIGITAL_MESSAGE, self._handle_digital_message)
        self.add_cmd_handler(REPORT_VERSION, self._handle_report_version)
        self.add_cmd_handler(REPORT_FIRMWARE, self._handle_report_firmware)
    
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
        a_d = bits[0] == 'a' and 'analog' or 'digital'
        part = getattr(self, a_d)
        pin_nr = int(bits[1])
        if pin_nr >= len(part):
            raise InvalidPinDefError('Invalid pin definition: %s at position 3 on %s' % (pin_def, self.name))
        if getattr(part[pin_nr], 'mode', None)  == UNAVAILABLE:
            raise InvalidPinDefError('Invalid pin definition: UNAVAILABLE pin %s at position on %s' % (pin_def, self.name))
        if self.taken[a_d][pin_nr]:
            raise PinAlreadyTakenError('%s pin %s is already taken on %s' % (a_d, bits[1], self.name))
        # ok, should be available
        pin = part[pin_nr]
        self.taken[a_d][pin_nr] = True
        if pin.type is DIGITAL:
            if bits[2] == 'p':
                pin.mode = PWM
            elif bits[2] is not 'o':
                pin.mode = INPUT
        else:
            pin.enable_reporting()
        return pin
        
    def pass_time(self, t):
        """ 
        Non-blocking time-out for ``t`` seconds.
        """
        cont = time.time() + t
        while time.time() < cont:
            time.sleep(0)
            
    def send_sysex(self, sysex_cmd, data=[]):
        """
        Sends a SysEx msg.
        
        :arg sysex_cmd: A sysex command byte
        :arg data: A list of data values
        """
        self.sp.write(chr(START_SYSEX))
        self.sp.write(chr(sysex_cmd))
        for byte in data:
            try:
                byte = chr(byte)
            except ValueError:
                byte = chr(byte >> 7) # TODO send multiple bytes
            self.sp.write(byte)
        self.sp.write(chr(END_SYSEX))
        
    def iterate(self):
        """ 
        Reads and handles data from the microcontroller over the serial port.
        This method should be called in a main loop, or in an
        :class:`Iterator` instance to keep this boards pin values up to date
        """
        self._process_data(self.sp.read())
        
    def _process_data(self, byte):
        """
        Does the actual processing of the data from the microcontroller and
        delegates the command processing to :method:`_process_command`
        """
        if not byte:
            return
        data = ord(byte)
        if self._parsing_sysex:
            if data == END_SYSEX:
                self._parsing_sysex = False
                if self._stored_data[0] in self._command_handlers:
                    self._process_command(self._stored_data[0], self._stored_data[1:])
                self._stored_data = []
            else:
                self._stored_data.append(data)
        elif not self._command:
            if data == START_SYSEX:
                self._parsing_sysex = True
                return
            elif data < 0xF0:
                # Commands can have 'channel data' like a pin nummber appended. 
                # This is for commands smaller than 0xF0
                command = data & 0xF0
                self._stored_data.append(data & 0x0F)
            else:
                command = data
            if command not in self._command_handlers:
                # We received a byte not denoting a command with handler 
                # while we are not processing any commands data. Nothing we
                # can do about it so discard everything and we'll see what 
                # comes next.
                self._stored_data = []
                return
            self._command = command
        else:
            # This is a data command either belonging to a sysex message, or
            # to a multibyte command. Append it to the data and see if we can
            # process the command. If _process_command returns False, it
            # needs more data.
            self._stored_data.append(data)
            if self._process_command(self._command, self._stored_data):
                self._command = None
                self._stored_data = []
    
    def _process_command(self, command, data):
        """
        Tries to get a handler for this command from the self.cmds helper.
        Will return True if command is handled. This means either the handler
        handled the data correctly, or it raised a ValueError for not getting
        in the correct data. It will return False if there wasn't enough data
        for the handler
        """
        # TODO document that a handler should 
        handler = self._command_handlers[command]
        if len(data) < handler.bytes_needed:
            return False
        try:
            handler(*data)
        except ValueError:
            return True
        return True
            
    def get_firmata_version(self):
        """
        Returns a version tuple (major, mino) for the firmata firmware on the
        board.
        """
        return self.firmata_version
        
    def exit(self):
        """ Call this to exit cleanly. """
        self.sp.close()
        
    # Command handlers
    def _handle_analog_message(self, pin_nr, lsb, msb):
        value = float((msb << 7) + lsb) / 1023
        # Only set the value if we are actually reporting
        if self.analog[pin_nr].reporting:
            self.analog[pin_nr].value = value
        return True

    def _handle_digital_message(self, port_nr, lsb, msb):
        """
        Digital messages always go by the whole port. This means we have a
        bitmask wich we update the port.
        """
        mask = (msb << 7) + lsb
        self.digital_ports[port_nr]._update(mask)
        return True

    def _handle_report_version(self, major, minor):
        self.firmata_version = (major, minor)
        return True
        
    def _handle_report_firmware(self, *data):
        major = data[0]
        minor = data[1]
        self.firmata_version = (major, minor)
        self.firmware = ''.join([chr(x) for x in data[2:]]) # TODO this is more complicated, values is send as 7 bit bytes
        return True

class Port(object):
    """ An 8-bit port on the board """
    def __init__(self, board, port_number):
        self.board = board
        self.port_number = port_number
        self.reporting = False
        
        self.pins = []
        for i in range(8):
            pin_nr = i + self.port_number * 8
            self.pins.append(Pin(self.board, pin_nr, type=DIGITAL, port=self))
            
    def __str__(self):
        return "Digital Port %i on %s" % (self.port_number, self.board)
        
    def enable_reporting(self):
        """ Enable reporting of values for the whole port """
        self.reporting = True
        msg = chr(REPORT_DIGITAL + self.port_number)
        msg += chr(1)
        self.board.sp.write(msg)
        
    def disable_reporting(self):
        """ Disable the reporting of the port """
        self.reporting = False
        msg = chr(REPORT_DIGITAL + self.port_number)
        msg += chr(0)
        self.board.sp.write(msg)
                
    def write(self):
        """Set the output pins of the port to the correct state"""
        mask = 0
        for pin in self.pins:
            if pin.mode == OUTPUT:
                if pin.value == 1:
                    pin_nr = pin.pin_number - self.port_number * 8
                    mask |= 1 << pin_nr
        msg = chr(DIGITAL_MESSAGE + self.port_number)
        msg += chr(mask % 128)
        msg += chr(mask >> 7)
        self.board.sp.write(msg)
        
    def _update(self, mask):
        """
        Update the values for the pins marked as input with the mask.
        """
        if self.reporting:
            for pin in self.pins:
                if pin.mode is INPUT:
                    pin.value = (mask & (1 << pin.pin_number)) > 1

class Pin(object):
    """ A Pin representation """
    def __init__(self, board, pin_number, type=ANALOG, port=None):
        self.board = board
        self.pin_number = pin_number
        self.type = type
        self.port = port
        self.PWM_CAPABLE = False
        self._mode = (type == DIGITAL and OUTPUT or INPUT)
        self.reporting = False
        self.value = None
        
    def __str__(self):
        type = {ANALOG : 'Analog', DIGITAL : 'Digital'}[self.type]
        return "%s pin %d" % (type, self.pin_number)

    def _set_mode(self, mode):
        """
        Set the mode of operation for the pin
        :arg mode: Can be one of the pin modes: INPUT, OUTPUT, ANALOG or PWM
        
        """
        if mode is UNAVAILABLE:
            self._mode = UNAVAILABLE
            return
        if mode is PWM and not self.PWM_CAPABLE:
            raise IOError, "%s does not have PWM capabilities" % self
        if self._mode is UNAVAILABLE:
            raise IOError, "%s can not be used through Firmata" % self
        self._mode = mode
        command = chr(SET_PIN_MODE)
        command += chr(self.pin_number)
        command += chr(mode)
        self.board.sp.write(command)
        if mode == INPUT:
            self.enable_reporting()
        
    def _get_mode(self):
        return self._mode
        
    mode = property(_get_mode, _set_mode)
    
    def enable_reporting(self):
        """ Set an input pin to report values """
        if self.mode is not INPUT:
            raise IOError, "%s is not an input and can therefore not report" % self
        if self.type == ANALOG:
            self.reporting = True
            msg = chr(REPORT_ANALOG + self.pin_number)
            msg += chr(1)
            self.board.sp.write(msg)
        else:
            self.port.enable_reporting() # TODO This is not going to work for non-optimized boards like Mega
        
    def disable_reporting(self):
        """ Disable the reporting of an input pin """
        if self.type == ANALOG:
            self.reporting = False
            msg = chr(REPORT_ANALOG + self.pin_number)
            msg += chr(0)
            self.board.sp.write(msg)
        else:
            self.port.disable_reporting() # TODO This is not going to work for non-optimized boards like Mega
    
    def read(self):
        """
        Returns the output value of the pin. This value is updated by the
        boards :meth:`Board.iterate` method. Value is alway in the range 0.0 - 1.0
        """
        if self.mode == UNAVAILABLE:
            raise IOError, "Cannot read pin %s"% self.__str__()
        return self.value
        
    def write(self, value):
        """
        Output a voltage from the pin

        :arg value: Uses value as a boolean if the pin is in output mode, or 
            expects a float from 0 to 1 if the pin is in PWM mode.
        
        """
        if self.mode is UNAVAILABLE:
            raise IOError, "%s can not be used through Firmata" % self
        if self.mode is INPUT:
            raise IOError, "%s is set up as an INPUT and can therefore not be written to" % self
        if value is not self.value:
            self.value = value
            if self.mode is OUTPUT:
                if self.port:
                    self.port.write()
                else:
                    msg = chr(DIGITAL_MESSAGE)
                    msg += chr(self.pin_number)
                    msg += chr(value)
                    self.board.sp.write(msg)
            elif self.mode is PWM:
                value = int(round(value * 255))
                msg = chr(ANALOG_MESSAGE + self.pin_number)
                msg += chr(value % 128)
                msg += chr(value >> 7)
                self.board.sp.write(msg)
                
    def send_sysex(self, sysex_cmd, data=[]):
        """
        Sends a SysEx msg.
        
        :arg sysex_cmd: A sysex command byte
        :arg data: A list of data values
        """
        # TODO make the boards send_sysex available to the pin
        self.board.sp.write(chr(START_SYSEX))
        self.board.sp.write(chr(sysex_cmd))
        for byte in data:
            try:
                byte = chr(byte)
            except ValueError:
                byte = chr(byte >> 7) # TODO send multiple bytes
            self.board.sp.write(byte)
        self.board.sp.write(chr(END_SYSEX))