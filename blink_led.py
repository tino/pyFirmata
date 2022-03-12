# importando os módulos
from pyfirmata import Arduino, pyfirmata
import time

pin = 13 # número da porta digital

board = Arduino() # or Arduino(port) define board
print("Comunicação iniciada com sucesso!")

board.digital[pin].mode = pyfirmata.OUTPUT # define o pino como saída

# Criar funções para ligar e desligar led
def turn_on_led():
    board.digital[pin].write(1) # 1 liga o led
def turn_off_led():
    board.digital[pin].write(0) # 0 desliga o led

while True:
    turn_on_led() # chamar função e ligar led
    time.sleep(1) # esperar 1 segundo
    turn_off_led() # chamar função e desligar led
    time.sleep(1)
