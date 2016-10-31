#!/usr/bin/env python
# 
# Copyright (c) 2012-2013, Fabian Affolter <fabian@affolter-engineering.ch>
#
# Released under the MIT license. See LICENSE file for details.
#
import os
import sys
import time
import signal
import pyfirmata
from gi.repository import Gtk

PORT = '/dev/ttyACM0'

class UI:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(os.getcwd(), 'pyfirmata-gui.ui'))
        self.window = self.builder.get_object('window')
        self.aboutdialog = self.builder.get_object('aboutdialog')
        self.bt_exit = self.builder.get_object('bt_exit')
        self.bt_on = self.builder.get_object('bt_on')
        self.bt_off = self.builder.get_object('bt_off')
        self.statusbar = self.builder.get_object('statusbar')
        self.imagemenuitem5 = self.builder.get_object('imagemenuitem5')
        self.imagemenuitem10 = self.builder.get_object('imagemenuitem10')

        self.spinbutton = Gtk.SpinButton()
        self.spinbutton = self.builder.get_object('spinbutton')
        self.spinbutton.connect("changed", self.on_spin_changed)

        self.window.connect('delete-event', self.quit)
        self.bt_on.connect('clicked', self.pin_high)
        self.bt_off.connect('clicked', self.pin_low)
        self.bt_exit.connect('clicked', self.quit)
        self.imagemenuitem5.connect('activate', self.quit)
        self.imagemenuitem10.connect('activate', self.show_aboutdialog)
        self.window.show_all()
        self.pin = None
        self.port = PORT
        self.board = pyfirmata.Arduino(self.port)
        self.statusbar.push(1, ("Connected to %s" % PORT))
        
    def show_aboutdialog(self, *args):
        self.aboutdialog.run()
        self.aboutdialog.hide()

    def quit(self, *args):
        Gtk.main_quit()

    def pin_high(self, pin):
        self.board.digital[int(self.pin)].write(1)
        
    def pin_low(self, pin):
        self.board.digital[int(self.pin)].write(0)

    def on_spin_changed(self, spin):
        self.pin = self.spinbutton.get_text()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    ui = UI()
    Gtk.main()
