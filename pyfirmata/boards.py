BOARDS = {
    'arduino' : {
        'digital' : tuple(x for x in range(20)),
        'analog' : (14, 15, 16, 17, 18, 19),
        'pwm' : (3, 5, 6, 9, 10, 11),
        'servo' : (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13), 
        'i2c' : (18, 19),
        'use_ports' : True,
        'unavailable' : (0, 1) # Rx, Tx, Crystal
    },
    'arduino_mega' : {
        'digital' : tuple(x for x in range(54)),
        'analog' : tuple(x for x in range(16)),
        'pwm' : (2, 3, 4, 5, 6, 7, 8, 9, 10 ,11, 12, 13, 44, 45, 46),
        'servo' : tuple(x for x in range(54)),
        'i2c' : (20, 21),
        'use_ports' : True,
        'unavailable' : (0, 1) # Rx, Tx, Crystal
    }
}
