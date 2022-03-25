arduPython
==========

arduPython é um Fork da pyFirmata, que é uma interface Python para Arduino que usa o protocolo [Firmata](http://firmata.org). É totalmente compatível com Firmata 2.1 e possui algumas funcionalidades da versão 2.2. Ele roda em Python 3.7, 3.8, 3.9 e 3.10. Com essa biblioteca você contralará a placa Arduino utilizando a linguagem Python. 

Na versão atual, você encontrará melhorias usando a última versão do Python (3.10) e suporte ao PulseIn (Ex.: para controlar o sensor HC-SR04) da linguagem Arduino.

Instalação
============

A maneira preferida de instalar é com [pip](http://www.pip-installer.org/en/latest/)::

    pip install arduPython==1.1.3

Você também pode instalar a partir do código-fonte com ``python setup.py install``. Você precisará ter [setuptools](https://pypi.python.org/pypi/setuptools) instalado ::

    git clone https://github.com/BosonsHiggs/arduPython.git
    cd pyFirmata
    python setup.py install


Uso
====

Uso básico::

    >>> from pyfirmata import Arduino, util
    >>> board = Arduino('/dev/tty.usbserial-A6008rIF') ou board = Arduino() 
    >>> board.digital[13].write(1)

Para usar portas analógicas, provavelmente é útil iniciar um encadeamento de iteradores. Caso contrário, a placa continuará enviando dados para o seu serial, até estourar:

    >>> it = util.Iterator(board)
    >>> it.start()
    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

Se você usa um pino com mais frequência, pode valer a pena usar o método ``get_pin`` da placa. Ele permite que você especifique qual pino você precisa por uma string, composta de 'a' ou 'd' (dependendo se você precisa de um pino analógico ou digital), o número do pino e o modo ('i' para entrada, 'o 'para saída,' p 'para pwm). Todos separados por ``:``. Por exemplo. ``a:0:i`` para 0 analógico como entrada ou ``d:3:p`` para pino digital 3 como pwm. ::

    >>> analog_0 = board.get_pin('a:0:i')
    >>> analog_0.read()
    0.661440304938
    >>> pin3 = board.get_pin('d:3:p')
    >>> pin3.write(0.6)

Layout de uma placa Arduino qualquer
====================================

Se você quiser usar uma placa com um layout diferente do Arduino padrão ou do Arduino Mega (para o qual existem as classes de atalho ``pyfirmata.Arduino`` e `` pyfirmata.ArduinoMega``), instancie a classe Board com um dicionário como o argumento `` layout``. Este é o ditado de layout para o Mega, por exemplo::

    >>> mega = {
    ...         'digital' : tuple(x for x in range(54)),
    ...         'analog' : tuple(x for x in range(16)),
    ...         'pwm' : tuple(x for x in range(2,14)),
    ...         'use_ports' : True,
    ...         'disabled' : (0, 1, 14, 15) # Rx, Tx, Crystal
    ...         }

Suporte ao Ping (pulseIn)
==========================

Se você quiser usar sensores de alcance ultrassônicos que usam um pulso para medir distâncias (como o muito barato e comum ``HC-SR04``
- Veja [datasheet](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf),
você precisará usar um Firmata compatível com ``pulseIn`` em sua placa.

Você pode baixá-lo da ramificação [``pulseIn``](https://github.com/jgautier/arduino-1/tree/pulseIn) do repositório Firmata:

Basta conectar os pinos ``Trig`` e ``Echo`` do sensor a um pino digital em sua placa.

![Fonte: https://github.com/NeoPolus/pyFirmata](Examples/ping.png)

E então use o método ping no pino:

    >>> echo_pin = board.get_pin('d:7:o')
    >>> echo_pin.ping()
    1204

Você pode usar a função ``ping_time_to_distance`` para converter
o resultado do ping (tempo de eco) em distância:

    >>> from pyfirmata.util import ping_time_to_distance
    >>> echo_pin = board.get_pin('d:7:o')
    >>> ping_time_to_distance(echo_pin.ping())
    20.485458055607776

Créditos
========

- [NeoPolus](https://github.com/NeoPolus/pyFirmata)
- [Tino](https://github.com/tino/pyFirmata)

Links
=====

- [Servidor Oficial na Discord](https://discord.gg/nPejnfC3Nu)
- Meu usuário na Discord: Aril Ogai#