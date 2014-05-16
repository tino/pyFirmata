BOARDS = {
    'arduino' : {
        'digital' : tuple(x for x in range(14)),
        'analog' : tuple(x for x in range(6)),
        'pwm' : (3, 5, 6, 9, 10, 11),
        #'servo' : (), # 2.2 specs
        #'i2c' : (), # 2.3 specs
        'disabled' : (0, 1) # Rx, Tx, Crystal
    },
    'arduino_mega' : {
        'digital' : tuple(x for x in range(54)),
        'analog' : tuple(x for x in range(16)),
        'pwm' : tuple(x for x in range(2,14)),
        #'servo' : (), # 2.2 specs
        #'i2c' : (), # 2.3 specs
        'disabled' : (0, 1) # Rx, Tx, Crystal
    }
}

def pinList2boardDict(pinlist):
    """
    Capability Response codes:
        INPUT:  0, 1
        OUTPUT: 1, 1
        ANALOG: 2, 10
        PWM:    3, 8
        SERV0:  4, 14
        I2C:    6, 1
    """

    boardDict = {
        'digital': [],
        'analog': [],
        'pwm': [],
        'servo': [], # 2.2 specs
        #'i2c': [], # 2.3 specs
        'disabled': [],
    }
    for i, pin in enumerate(pinlist):
        pin.pop() # removes the 0x79 on end
        if not pin:
            boardDict['disabled'] += [i]
            boardDict['digital'] += [i]
            continue

        for j, _ in enumerate(pin):
            # Iterate over evens
            if j % 2 == 0:
                # This is safe. try: range(10)[5:50]
                if pin[j:j+4] == [0, 1, 1, 1]:
                    boardDict['digital'] += [i]

                if pin[j:j+2] == [2, 10]:
                    boardDict['analog'] += [i]

                if pin[j:j+2] == [3, 8]:
                    boardDict['pwm'] += [i]

                if pin[j:j+2] == [4, 14]:
                    boardDict['servo'] += [i]

                # Desable I2C
                if pin[j:j+2] == [6, 1]:
                    #boardDict['i2c'] += [i]
                    pass

    # We have to deal with analog pins:
    # - (14, 15, 16, 17, 18, 19)
    # + (0, 1, 2, 3, 4, 5)
    diff = set(boardDict['digital']) - set(boardDict['analog'])
    boardDict['analog'] = [n for n, _ in enumerate(boardDict['analog'])]

    # Digital pin problems:
    #- (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
    #+ (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)

    boardDict['digital'] = [n for n, _ in enumerate(diff)]
    # TODO: set 'servo' right
    boardDict['servo'] = [n for n, _ in enumerate(boardDict['servo'])]

    # Turn lists into tuples
    boardDict = {
            key: tuple(value)
            for key, value
            in boardDict.items()
    }

    return boardDict

