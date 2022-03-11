#Módulos necessários
from pyfirmata import Arduino, pyfirmata, util
import time

##Portas analógicas dos LDRs
led1PullDw = 0
led2PullUp = 1

#Identificando a placa
board = Arduino() # or Arduino(port) define board
print("Comunicação iniciada com sucesso!")

## Iniciando Iterador
"""Para usar portas analógicas, provavelmente é útil iniciar um encadeamento iterador. 
   Caso contrário, a placa continuará enviando dados para o seu serial, até transbordar:"""
it = util.Iterator(board)
it.start()

##Configurando estado dos pinos
ldr1 = board.get_pin(f'a:{led1PullDw}:i') #a = analog and i = input
ldr2 = board.get_pin(f'a:{led2PullUp}:i') #a = analog and i = input

##Iniciando
ldr1.enable_reporting()
ldr2.enable_reporting()

while True:
    ## Ler LDRs
    ldr1_ = ldr1.read()
    ldr2_ = ldr2.read()
    print(f'LDR PullDown: {ldr1_}, LDR PullUp: {ldr2_}')
    time.sleep(0.3) #300 milissegundos ou 300ms