from serial import SerialException
import threading
import util
from boards import BOARDS

# Message command bytes - straight from Firmata.h
DIGITAL_MESSAGE = 0x90,      # send data for a digital pin
ANALOG_MESSAGE = 0xE0,       # send data for an analog pin (or PWM)
DIGITAL_PULSE = 0x91,        # SysEx command to send a digital pulse

# PULSE_MESSAGE = 0xA0,      # proposed pulseIn/Out msg (SysEx)
# SHIFTOUT_MESSAGE = 0xB0,   # proposed shiftOut msg (SysEx)
REPORT_ANALOG = 0xC0,        # enable analog input by pin #
REPORT_DIGITAL = 0xD0,       # enable digital input by port pair
START_SYSEX = 0xF0,          # start a MIDI SysEx msg
SET_PIN_MODE = 0xF4,         # set a pin to INPUT/OUTPUT/PWM/etc
END_SYSEX = 0xF7,            # end a MIDI SysEx msg
REPORT_VERSION = 0xF9,       # report firmware version
SYSTEM_RESET = 0xFF,         # reset from MIDI

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
    
    def __init__(self, port, type="arduino", baudrate=57600):
        self.type = type
        self.setup_layout(BOARDS[type])
        self.command_handlers = dict()
        self.sp = serial.Serial(port, baudrate)
        # Allow 2 secs for Arduino's auto-reset to happen
        self.pass_time(2)
        
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
            self.analog.append(Pin(self.sp, i, board_name=self.name))
        # Only create digital ports if the Firmata can use them (ie. not on the Mega...)
        # TODO Why is (TOTAL_FIRMATA_PINS + 7) / 8 used in Firmata?
        if board_layout['use_ports']:
            self.digital = []
            self.digital_ports = []
            for i in range(len(board_layout['digital']) / 7):
                self.digital_ports.append(Port(self.sp, i, self))
            # Allow to access the Pin instances directly
            for port in self.digital_ports:
                self.digital += port.pins
            for i in board_layout['pwm']:
                self.digital[i].PWM_CAPABLE = True
        else:
            self.digital = []
            for i in board_layout['digital']:
                self.digital.append(Pin(self.sp, i, type=DIGITAL, board_name=self.name))
        # Disable certain ports like Rx/Tx and crystal ports
        for i in board_layout['disabled']:
            self.digital[i].mode = UNAVAILABLE
        # Create a dictionary of 'taken' pins. Used by the get_pin method
        self.taken = { 'analog' : dict(map(lambda p: (p.pin_number, False), self.analog)),
                       'digital' : dict(map(lambda p: (p.pin_number, False), self.digital)) }
        # Setup default handlers for standard incoming commands
        self.command_handlers[ANALOG_MESSAGE] = self._handle_analog_message
        self.command_handlers[DIGITAL_MESSAGE] =  self._handle_digital_message
        self.command_handlers[REPORT_VERSION] = self._handle_report_version
        
        
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
        byte = ord(byte)
        if self._parsing_sysex:
            if byte == END_SYSEX:
                self._parsing_sysex = False
                self._process_sysex_message(self._stored_data)
                self._stored_data = []
            else:
                self._stored_data.append(byte)
        elif not self._command:
            if byte not in self.command_handlers:
                # We received a byte not denoting a command with handler 
                # while we are not processing any commands data. Nothing we
                # can do about it so discard and we'll see what comes next.
                return
            self._command = byte
        else:
            # This is a data command either belonging to a sysex message, or
            # to a multibyte command. Append it to the data and see if we can
            # process the command. If _process_command returns False, it
            # needs more data.
            self._stored_data.append(byte)
            try:
                if self._process_command(self._command, self._stored_data):
                    self._command = None
                    self._stored_data = []
            except ValueError:
                self._command = None
                self._stored_data = []
    
    def _process_command(command, data):
        """
        Tries to get a handler for this command from the self.cmds helper and will
        return its return status.
        """
        try:
             handle_cmd = self.command_handlers[command]
             return handle_cmd(self, data)
        except (KeyError, ValueError):
            # something got corrupted
            raise ValueError
            
    def _process_sysex_message(self, data):
        # TODO implement or make _process_command deal with it
        pass
            
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
    def _handle_analog_message(self, data):
        if len(data) < 3:
            return False
        pin_number, lsb, msb = data
        value = float(msb << 7 | lsb) / 1023
        self.analog[pin_number].value = value
        return True

    def _handle_digital_message(self, data):
        if len(data) < 3:
            return False
        pin_number, lsb, msb = data
        value = msb << 7 | lsb
        self.digital[pin_number].value = value
        return True

    def _handle_report_version(self, data):
        if len(data) < 3:
            return False
        major, minor = data
        self.firmata_version = (major, minor)

        

class Port(object):
    """ An 8-bit port on the board """
    def __init__(self, sp, port_number, board):
        self.board = board
        self.sp = sp
        self.port_number = port_number
        self.reporting = False
        
        self.pins = []
        for i in range(8):
            pin_nr = i + self.port_number * 8
            self.pins.append(Pin(sp, pin_nr, type=DIGITAL, port=self, board_name=self.board.name))
            
    def __str__(self):
        return "Digital Port %i on %s" % (self.port_number, self.board)
        
    def enable_reporting(self):
        """ Enable reporting of values for the whole port """
        self.reporting = True
        msg = chr(REPORT_DIGITAL + self.port_number + 1)
        self.sp.write(msg)
        
    def disable_reporting(self):
        """ Disable the reporting of the port """
        self.reporting = False
        msg = chr(REPORT_DIGITAL + self.port_number + 0)
        self.sp.write(msg)
        
    def set_value(self, mask):
        """Record the value of each of the input pins belonging to the port"""
        
        for pin in self.pins:
            if pin.mode is INPUT:
                pin.set_value((mask & (1 << pin.pin_number)) > 1)
                
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
        self.sp.write(msg)

class Pin(object):
    """ A Pin representation """
    def __init__(self, sp, pin_number, type=ANALOG, board_name=None, port=None):
        self.sp = sp
        self.pin_number = pin_number
        self.type = type
        self.board_name = board_name
        self.port = port
        self.PWM_CAPABLE = False
        self._mode = (type == DIGITAL and OUTPUT or INPUT)
        self.reporting = False
        self.value = None
        
    def __str__(self):
        type = {ANALOG : 'Analog', DIGITAL : 'Digital'}[self.type]
        if self.board_name:
            return "%s pin %d on %s" % (type, self.pin_number, self.board_name)
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
        self.sp.write(command)
        
    def _get_mode(self):
        return self._mode
        
    mode = property(_get_mode, _set_mode)
    
    def enable_reporting(self):
        """ Set an input pin to report values """
        if self.mode is not INPUT:
            raise IOError, "%s is not an input and can therefore not report" % self
        self.reporting = True
        msg = chr(REPORT_ANALOG + self.pin_number)
        msg += chr(1)
        self.sp.write(msg)
        
    def disable_reporting(self):
        """ Disable the reporting of an input pin """
        self.reporting = False
        msg = chr(REPORT_ANALOG + self.pin_number)
        msg += chr(0)
        self.sp.write(msg)
    
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
                    self.sp.write(msg)
            elif self.mode is PWM:
                value = int(round(value * 255))
                msg = chr(ANALOG_MESSAGE + self.pin_number)
                msg += chr(value % 128)
                msg += chr(value >> 7)
                self.sp.write(msg)
                
    def send_sysex(self, sysex_cmd, data=[]):
        """
        Sends a SysEx msg.
        
        :arg sysex_cmd: A sysex command byte
        :arg data: A list of data values
        """
        # TODO make the boards send_sysex available to the pin
        self.sp.write(chr(START_SYSEX))
        self.sp.write(chr(sysex_cmd))
        for byte in data:
            try:
                byte = chr(byte)
            except ValueError:
                byte = chr(byte >> 7) # TODO send multiple bytes
            self.sp.write(byte)
        self.sp.write(chr(END_SYSEX))