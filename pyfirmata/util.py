import threading
import serial
import time
import pyfirmata

class Boards(dict):
    """
    A dictonary to manage multiple boards on the same machine. Tries to
    connect to all defined usb ports, and then tries to fetch the board's
    name. Result is a dictionary of `Board`_ classes mapped to their names.
    """
    def __init__(self, base_dir='/dev/', identifier='tty.usbserial', boards_map=None):
        """
        Searches all possible USB devices in ``base_dir`` that start with
        ``identifier``. If given an ``boards_map`` dictionary it will setup
        the boards in the map according to their type. Finding a board that
        does not identify itself at all, that are not in the map, or boards
        that are missing fail silenly. Use the ``verify_found_boards`` method
        to check this.
        
        :base_dir arg: A absolute path for the base directory to search for USB connections
        :identifier arg: A string a USB connection startswith and should be tried
        :boards_map arg: A dictionary in the form of::
            boards_map = { 1 : {'name' : 'myduino', 'board' : 'board'},
                           2 : {'name' : 'mymega', 'board' : 'board_mega'} }
        """
        for device in os.listdir(base_dir):
            if device.startswith(identifier):
                try:
                    board = pyfirmata.Board(os.path.join(base_dir, device))
                except SerialException:
                    pass
                else:
                    # if board.id:
                    #     try:
                    #         board.name = boards_map[board.id]['name']
                    #         board.setup_layout(pyfirmata.BOARDS[boards_map[board.id]['board']])
                    #     except (KeyError, TypeError): # FIXME Possible KeyErrors from setup_layout are caught here...
                    #         # FIXME Better to check if boards_map is valid if given, otherwise raise error
                    #         pass
                    # if not board.name:
                    board_name = 'unknown-%s' % device[-5:-1]
                    self[board_name] = board
                            
    def verify_found_boards(self, boards_map):
        """
        Returns True if all and only boards in the map are found. Returns
        False otherwise
        """
        names = set()
        for board in boards_map:
            names.add(board['name'])
        return names is set(self.keys())
        
    def get_pin(self, pin_def):
        parts = pin_def.split(':')
        try:
            return self[parts[0]].get_pin([parts[1], parts[2], parts[3]])
        except KeyError:
            raise KeyError("board named %s not found" % parts[0])
        except IndexError:
            raise pyfirmata.InvalidPinDefError("%s is not a valid pin definition" % pin_def)
            
    def exit(self):
        for board in self.values():
            board.exit()
            
    def __del__(self):
        ''' 
        The connection with the board can get messed up when a script is
        closed without calling board.exit() (which closes the serial
        connection). Therefore do it here and hope it helps.
        '''
        self.exit()

def get_the_board(base_dir='/dev/', identifier='tty.usbserial',):
    """
    Helper function to get the one and only board connected to the computer
    running this. It does needs the ``base_dir`` and ``identifier`` though. It
    will raise an IOError if it can't find a board, on a serial, or if it
    finds more than one.
    """
    boards = Boards(base_dir='/dev/', identifier='tty.usbserial')
    if len(boards) == 0:
        raise IOError, "No boards found in %s with identifier %s" % (base_dir, identifier)
    elif len(boards) > 1:
        raise IOError, "More than one board found!"
    return boards[boards.keys()[0]]

class Iterator(threading.Thread):
    def __init__(self, board):
        super(Iterator, self).__init__()
        self.board = board
        
    def run(self):
        while 1:
            try:
                while self.board.iterate():
                    self.board.iterate()
                time.sleep(0.001)
            except (AttributeError, serial.SerialException, OSError), e:
                # this way we can kill the thread by setting the board object
                # to None, or when the serial port is closed by board.exit()
                break
            except Exception, e:
                # catch 'error: Bad file descriptor'
                # iterate may be called while the serial port is being closed,
                # causing an "error: (9, 'Bad file descriptor')"
                if getattr(e, 'errno', None) == 9:
                    break
                try:
                    if e[0] == 9:
                        break
                except (TypeError, IndexError):
                    pass
                raise
                
def to_7_bits(integer):
    """
    Breaks an integer into two 7 bit bytes.
    
    >>> for i in range(32768):
    ...     val = to_7_bits(i)
    ...     assert len(val) == 2
    ...
    >>> to_7_bits(32767)
    ('\\x7f', '\\xff')
    >>> to_7_bits(32768)
    Traceback (most recent call last):
        ...
    ValueError: Can't handle values bigger than 32767 (max for 2 bits)
    
    """
    if integer > 32767:
        raise ValueError, "Can't handle values bigger than 32767 (max for 2 bits)"
    return chr(integer % 128), chr(integer >> 7)

def break_to_bytes(value):
    """
    Breaks a value into values of less than 255 that form value when multiplied.
    (Or almost do so with primes)
    Returns a tuple
    
    >>> break_to_bytes(200)
    (200,)
    >>> break_to_bytes(800)
    (200, 4)
    >>> break_to_bytes(802)
    (2, 2, 200)
    """
    if value < 256:
        return (value,)
    c = 256
    least = (0, 255)
    for i in range(254):
        c -= 1
        rest = value % c
        if rest == 0 and value / c < 256:
            return (c, value / c)
        elif rest == 0 and value / c > 255:
            parts = list(break_to_bytes(value / c))
            parts.insert(0, c)
            return tuple(parts)
        else:
            if rest < least[1]:
                least = (c, rest)
    return (c, value / c)

if __name__ == '__main__':
    import doctest
    doctest.testmod()