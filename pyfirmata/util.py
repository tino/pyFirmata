import threading
import serial

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
                # this way we can kill the thread by setting the arduino object
                # to None, or when the serial port is closed by arduino.exit()
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