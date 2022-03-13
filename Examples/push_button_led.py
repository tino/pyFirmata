# import modules
from pyfirmata import Arduino, pyfirmata, util
import time

buttonRead = False
pushButton = 8
ledPin = 9

board = Arduino() # or Arduino(port) define board
print("Communication successfully started!")

board.digital[ledPin].mode = pyfirmata.OUTPUT # define output mode

# create function to turn on and off led
def turn_on_led(pin_):
    board.digital[pin_].write(1) # 1 means power on

def turn_off_led(pin_):
    board.digital[pin_].write(0) # 0 means power off

button = board.get_pin(f'd:{pushButton}:i') #definindo pino
button.enable_reporting() #abrir leitura de valores nesse pino

""" util.Iterator()
Lê e manipula dados do microcontrolador pela porta serial. 
Este método deve ser chamado em um loop principal ou em uma 
Iterator instância para manter os valores dos pinos das placas atualizados.
"""
iterator = util.Iterator(board)
iterator.start()

while True:
   
    buttonRead = button.read() #ler valores 
    print(button.read())
    time.sleep(0.075)

    if buttonRead:
        turn_on_led(ledPin) # call the function
    else:
        print( 'Desligando')
        turn_off_led(ledPin) # call the function
    
    board.pass_time(1)

board.exit()