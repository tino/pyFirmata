BOARDS = {
    'arduino': {
        'digital': tuple(x for x in range(14)),
        'analog': tuple(x for x in range(6)),
        'pwm': (3, 5, 6, 9, 10, 11),
        'use_ports': True,
        'disabled': (0, 1)  # Rx, Tx, Crystal
    },
    'arduino_mega': {
        'digital': tuple(x for x in range(54)),
        'analog': tuple(x for x in range(16)),
        'pwm': tuple(x for x in range(2, 14)),
        'use_ports': True,
        'disabled': (0, 1)  # Rx, Tx, Crystal
    },
    'arduino_due': {
        'digital': tuple(x for x in range(54)),
        'analog': tuple(x for x in range(12)),
        'pwm': tuple(x for x in range(2, 14)),
        'use_ports': True,
        'disabled': (0, 1)  # Rx, Tx, Crystal
    },
    'arduino_nano': {
        'digital': tuple(x for x in range(14)),
        'analog': tuple(x for x in range(8)),
        'pwm': (3, 5, 6, 9, 10, 11),
        'use_ports': True,
        'disabled': (0, 1)  # Rx, Tx, Crystal
    }
}
