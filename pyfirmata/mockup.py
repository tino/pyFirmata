import pyfirmata

class MockupSerial(object):
    """ A Mockup object for python's Serial. Can only return Firmata version. """
    def __init__(self, port, baudrate, timeout=1):
        self.return_id = False
        self.echoed = False
        
    def read(self, len=1):
        if self.return_id:
            if self.echoed:
                self.return_id = False
                return chr(1)
            else:
                self.echoed = True
                return chr(pyfirmata.REPORT_ARDUINO_ID)
        else:
            return ''
            
    def write(self, value):
        if value == chr(pyfirmata.REPORT_ARDUINO_ID):
            self.return_id = True
            
    def close(self):
        pass

class MockupArduinos(pyfirmata.Arduinos):
    def __init__(self, identifier='', arduinos_map={}, values_dict={}):
        self.values_dict = values_dict
        for a in arduinos_map.values():
            self[a['name']] = MockupArduino(name=a['name'], type=a['board'], values_dict=values_dict)
        
    def update_values_dict(self, values_dict=None):
        if values_dict is not None:
            self.values_dict.update(values_dict)
        if values_dict == {}: # reset
            self.values_dict = {}
        self['gen'].values_dict = self.values_dict
        self['gen'].update_values_dict()
    
    def reset_taken(self):
        self['gen'].reset_taken()
        
class MockupArduino(pyfirmata.Arduino):

    def __init__(self, port='', type="normal", values_dict={}, name=''):
        self.name = name
        self.sp = MockupSerial(port, 57600, timeout=0)
        self.setup_layout(pyfirmata.BOARDS[type])
        self.values_dict = values_dict
        self.id = 1
        
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
        
class MockupPort(pyfirmata.DigitalPort):
    def __init__(self, sp, port_number):
        self.sp = sp
        self.port_number = port_number
        self.reporting = False
        
        self.pins = []
        for i in range(8):
            pin_nr = i + self.port_number * 8
            self.pins.append(MockupPin(sp, pin_nr, type=pyfirmata.DIGITAL, port=self))

    def update_values_dict(self):
        for pin in self.pins:
            pin.values_dict = self.values_dict
        
class MockupPin(pyfirmata.Pin):
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
        if not self.port and not self.mode: # analog input
            return 'i'
        else:
            return 'o'
            
    def set_active(self, active):
        self.is_active = active
        
    def get_active(self):
        return self.is_active
        
    def write(self, value):
        if self.mode == pyfirmata.UNAVAILABLE:
            raise IOError, "Cannot read from pin %d" \
                           % (self.pin_number)
        if self.mode == pyfirmata.INPUT:
            raise IOError, "%s pin %d is not an output" \
                            % (self.port and "Digital" or "Analog", self.get_pin_number())
        if not self.port:
            raise AttributeError, "AnalogPin instance has no attribute 'write'"
        # if value != self.read():
        self.value = value
        
class Iterator(object):
    def __init__(self, *args, **kwargs):
        pass
    def start(self):
        pass
    def stop(self):
        pass

pyfirmata.DigitalPort = MockupPort
pyfirmata.Pin = MockupPin

Arduinos = MockupArduinos
Arduino = MockupArduino