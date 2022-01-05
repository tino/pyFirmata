=========
arduPython
=========

arduPython é um Fork da pyFirmata, onde é uma interface Python para o protocolo `Firmata`_. É totalmente compatível com Firmata 2.1 e possui algumas funcionalidades da versão 2.2. Ele roda em Python 2.7, 3.6 e 3.7.

.. _Firmata: http://firmata.org

Instalação
============

A maneira preferida de instalar é com pip_::

    pip install audupython

Você também pode instalar a partir do código-fonte com ``python setup.py install``. Você precisará ter `setuptools`_ instalado ::

    git clone https://github.com/BosonsHiggs/arduPython.git
    cd pyFirmata
    python setup.py install

.. _pip: http://www.pip-installer.org/en/latest/
.. _setuptools: https://pypi.python.org/pypi/setuptools


Uso
=====

Uso básico::

    >>> from pyfirmata import Arduino, util
    >>> board = Arduino('/dev/tty.usbserial-A6008rIF')
    >>> board.digital[13].write(1)

Para usar portas analógicas, provavelmente é útil iniciar um encadeamento de iteradores. Caso contrário, a placa continuará enviando dados para o seu serial, até estourar:

    >>> it = util.Iterator(board)
    >>> it.start()
    >>> board.analog[0].enable_reporting()
    >>> board.analog[0].read()
    0.661440304938

Se você usa um pino com mais frequência, pode valer a pena usar o método ``get_pin`` da placa. Ele permite que você especifique qual pino você precisa por uma string, composta de 'a' ou 'd' (dependendo se você precisa de um pino analógico ou digital), o número do pino e o modo ('i' para entrada, 'o 'para saída,' p 'para pwm). Todos separados por ``:``. Por exemplo. `` a: 0: i`` para 0 analógico como entrada ou ``d: 3: p`` para pino digital 3 como pwm. ::

    >>> analog_0 = board.get_pin('a:0:i')
    >>> analog_0.read()
    0.661440304938
    >>> pin3 = board.get_pin('d:3:p')
    >>> pin3.write(0.6)

Layout de uma placa Arduino qualquer
============

Se você quiser usar uma placa com um layout diferente do Arduino padrão ou do Arduino Mega (para o qual existem as classes de atalho ``pyfirmata.Arduino`` e `` pyfirmata.ArduinoMega``), instancie a classe Board com um dicionário como o argumento `` layout``. Este é o ditado de layout para o Mega, por exemplo::

    >>> mega = {
    ...         'digital' : tuple(x for x in range(54)),
    ...         'analog' : tuple(x for x in range(16)),
    ...         'pwm' : tuple(x for x in range(2,14)),
    ...         'use_ports' : True,
    ...         'disabled' : (0, 1, 14, 15) # Rx, Tx, Crystal
    ...         }

Conflitos
========

As próximas coisas na nossa lista são implementar as novas mudanças de protocolo no firmata:

- Pin State Query, que permite preencher os controles na tela com uma representação precisa da configuração do hardware (http://firmata.org/wiki/Proposals#Pin_State_Query_.28added_in_version_2.2.29)
